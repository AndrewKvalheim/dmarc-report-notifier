from email.message import EmailMessage
from json import dumps as as_json
from logging import basicConfig as configureLogging, info
from html import escape as as_html
from os import environ
from parsedmarc import get_dmarc_reports_from_mailbox
from parsedmarc.mail import IMAPConnection
from smtplib import SMTP


configureLogging(level=environ.get('LOG_LEVEL', 'INFO'))


def main():
    config = {
        'imap_host': environ['IMAP_HOST'],
        'imap_username': environ['IMAP_USERNAME'],
        'imap_password': environ['IMAP_PASSWORD'],
        'imap_folder_processed': environ['IMAP_FOLDER_PROCESSED'],
        'imap_folder_unprocessed': environ['IMAP_FOLDER_UNPROCESSED'],
        'smtp_host': environ['SMTP_HOST'],
        'smtp_port': int(environ['SMTP_PORT']),
        'smtp_username': environ['SMTP_USERNAME'],
        'smtp_password': environ['SMTP_PASSWORD'],
        'sender': environ['SENDER'],
        'recipient': environ['RECIPIENT'],
    };

    reports = get_dmarc_reports_from_mailbox(
        connection=IMAPConnection(
            host=config['imap_host'],
            user=config['imap_username'],
            password=config['imap_password']
        ),
        reports_folder=config['imap_folder_unprocessed'],
        archive_folder=config['imap_folder_processed']
    )

    notification_issues, notification_reports = set(), []
    for report in reports['aggregate_reports']:
        issues = set()
        for record in report['records']:
            if record['policy_evaluated']['dkim'] == 'fail': issues.add('DKIM failure')
            elif not record['alignment']['dkim']: issues.add('DKIM misalignment')
            if record['policy_evaluated']['spf'] == 'fail': issues.add('SPF failure')
            elif not record['alignment']['spf']: issues.add('SPF misalignment')
        info('Report %s from %s: %s',
            report['report_metadata']['report_id'],
            report['report_metadata']['org_name'],
            ', '.join(issues) if issues else 'OK'
        )
        if issues:
            notification_issues.update(issues)
            notification_reports.append(report)

    if notification_issues:
        info('Send email: from %s, to %s', config['sender'], config['recipient'])

        html = ''.join([f"<h2>{as_html(report['report_metadata']['org_name'])}</h2><pre>{as_html(as_json(report, ensure_ascii=False, indent=2))}</pre>" for report in notification_reports])

        message = EmailMessage()
        message['From'] = config['recipient']
        message['To'] = config['sender']
        message['Subject'] = ', '.join(notification_issues)
        message.set_content(html, subtype='html')

        with SMTP(config['smtp_host'], config['smtp_port']) as smtp:
            smtp.starttls()
            smtp.login(config['smtp_username'], config['smtp_password'])
            smtp.send_message(message)
            smtp.close()


if __name__ == '__main__':
    main()
