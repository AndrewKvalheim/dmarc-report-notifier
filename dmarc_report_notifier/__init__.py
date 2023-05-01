import asyncio
from jinja2 import Environment, PackageLoader, select_autoescape
from jinja2_pluralize import pluralize_dj
from logging import (
    basicConfig as configureLogging,
    getLevelName,
    info,
    ERROR,
    INFO,
    WARN,
)
from nio import (
    AsyncClient,
    JoinedRoomsResponse,
    JoinResponse,
    RoomSendResponse,
    WhoamiResponse,
)
from os import environ
from parsedmarc import get_dmarc_reports_from_mailbox
from parsedmarc.mail import IMAPConnection


configureLogging(level=environ.get("LOG_LEVEL", "INFO"))


def view(passed_fully, passed_partially, failed):
    environment = Environment(
        autoescape=select_autoescape(["html.j2"]),
        loader=PackageLoader(__package__),
    )
    environment.filters["pluralize"] = pluralize_dj
    context = {
        "failed": failed,
        "passed_fully": passed_fully,
        "passed_partially": passed_partially,
    }

    return {
        type: environment.get_template(f"message.{type}.j2").render(context)
        for type in ("html", "text")
    }


async def main():
    config = {
        "imap_host": environ["IMAP_HOST"],
        "imap_username": environ["IMAP_USERNAME"],
        "imap_password": environ["IMAP_PASSWORD"],
        "imap_folder_processed": environ["IMAP_FOLDER_PROCESSED"],
        "imap_folder_unprocessed": environ["IMAP_FOLDER_UNPROCESSED"],
        "matrix_access_token": environ["MATRIX_ACCESS_TOKEN"],
        "matrix_homeserver_url": environ["MATRIX_HOMESERVER_URL"],
        "matrix_room_id": environ["MATRIX_ROOM_ID"],
        "notification_level": getLevelName(environ.get("NOTIFICATION_LEVEL", "WARN")),
    }

    reports = get_dmarc_reports_from_mailbox(
        connection=IMAPConnection(
            host=config["imap_host"],
            user=config["imap_username"],
            password=config["imap_password"],
        ),
        reports_folder=config["imap_folder_unprocessed"],
        archive_folder=config["imap_folder_processed"],
    )["aggregate_reports"]

    passed_fully, passed_partially, failed = [], [], []
    for report in reports:
        for record in report["records"]:
            id = "{}/{}".format(
                report["report_metadata"]["report_id"], record["source"]["ip_address"]
            )
            result = record["policy_evaluated"]

            record["report_metadata"] = report["report_metadata"]

            if result["disposition"] == "none":
                if result["spf"] == "pass" and result["dkim"] == "pass":
                    info("Passed: %s", id)
                    if config["notification_level"] <= INFO:
                        passed_fully.append(record)
                else:
                    info("Passed with issues: %s", id)
                    if config["notification_level"] <= WARN:
                        passed_partially.append(record)
            else:
                info("Failed: %s", id)
                if config["notification_level"] <= ERROR:
                    failed.append(record)

    if passed_fully or passed_partially or failed:
        matrix = AsyncClient(config["matrix_homeserver_url"])
        matrix.access_token = config["matrix_access_token"]
        response = await matrix.whoami()
        assert isinstance(response, WhoamiResponse), response
        matrix.user_id = response.user_id
        info("Authenticated as %s", matrix.user_id)

        response = await matrix.joined_rooms()
        assert isinstance(response, JoinedRoomsResponse), response
        if config["matrix_room_id"] not in response.rooms:
            info("Join %s", config["matrix_room_id"])
            response = await matrix.join(config["matrix_room_id"])
            assert isinstance(response, JoinResponse), response

        body = view(passed_fully, passed_partially, failed)

        info("Send message in %s", config["matrix_room_id"])
        response = await matrix.room_send(
            room_id=config["matrix_room_id"],
            message_type="m.room.message",
            content={
                "msgtype": "m.notice",
                "body": body["text"],
                "format": "org.matrix.custom.html",
                "formatted_body": body["html"],
            },
        )
        assert isinstance(response, RoomSendResponse), response

        await matrix.close()


def main_sync():
    asyncio.run(main())
