import asyncio
from json import dumps as as_json
from logging import basicConfig as configureLogging, info
from html import escape as as_html
from nio import AsyncClient, JoinResponse
from os import environ
from parsedmarc import get_dmarc_reports_from_mailbox
from parsedmarc.mail import IMAPConnection


configureLogging(level=environ.get("LOG_LEVEL", "INFO"))


def view(notification_issues, notification_reports):
    summary = ", ".join(notification_issues)

    return f"<p>{summary}</p>" + "".join([view_report(r) for r in notification_reports])


def view_report(report):
    reporter = report["report_metadata"]["org_name"]
    json = as_json(report, ensure_ascii=False, indent=2)

    return f"<details><summary>Report from {as_html(reporter)}</summary><pre>{as_html(json)}</pre></details>"


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
    }

    reports = get_dmarc_reports_from_mailbox(
        connection=IMAPConnection(
            host=config["imap_host"],
            user=config["imap_username"],
            password=config["imap_password"],
        ),
        reports_folder=config["imap_folder_unprocessed"],
        archive_folder=config["imap_folder_processed"],
    )

    notification_issues, notification_reports = set(), []
    for report in reports["aggregate_reports"]:
        issues = set()
        for record in report["records"]:
            if record["policy_evaluated"]["dkim"] == "fail":
                issues.add("DKIM failure")
            elif not record["alignment"]["dkim"]:
                issues.add("DKIM misalignment")
            if record["policy_evaluated"]["spf"] == "fail":
                issues.add("SPF failure")
            elif not record["alignment"]["spf"]:
                issues.add("SPF misalignment")
        info(
            "Report %s from %s: %s",
            report["report_metadata"]["report_id"],
            report["report_metadata"]["org_name"],
            ", ".join(issues) if issues else "OK",
        )
        if issues:
            notification_issues.update(issues)
            notification_reports.append(report)

    if notification_issues:
        matrix = AsyncClient(config["matrix_homeserver_url"])
        matrix.access_token = config["matrix_access_token"]
        matrix.user_id = (await matrix.whoami()).user_id
        info("Authenticated as %s", matrix.user_id)

        if config["matrix_room_id"] not in (await matrix.joined_rooms()).rooms:
            info("Join %s", config["matrix_room_id"])
            response = await matrix.join(config["matrix_room_id"])
            assert isinstance(response, JoinResponse), response

        text = ", ".join(notification_issues)
        html = view(notification_issues, notification_reports)

        info("Send message in %s", config["matrix_room_id"])
        await matrix.room_send(
            room_id=config["matrix_room_id"],
            message_type="m.room.message",
            content={
                "msgtype": "m.notice",
                "body": text,
                "format": "org.matrix.custom.html",
                "formatted_body": html,
            },
        )

        await matrix.close()


def main_sync():
    asyncio.run(main())
