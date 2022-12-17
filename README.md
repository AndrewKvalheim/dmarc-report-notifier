# DMARC report notifier

*DMARC report notifier* is a headless periodic handler of [DMARC] aggregate reports. In contrast to other solutions to DMARC report monitoring that pursue elaborate web dashboards designed to guide an organization through policy rollouts and infrastructure changes, this utility is intended to fill the gap for low-volume senders with already aligned infrastructure that just need to do the minimum due diligence of being alerted to unexpected problems.

Intended to be scheduled as a daily job, this uses [parsedmarc] to read DMARC reports from a specified IMAP folder and then move them to an archive in the same mailbox. If any reports indicate a problem, a notification is sent via SMTP.


[DMARC]: https://en.wikipedia.org/wiki/DMARC
[parsedmarc]: https://github.com/domainaware/parsedmarc
