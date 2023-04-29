# DMARC report notifier

*DMARC report notifier* is a headless periodic handler of [DMARC] aggregate reports. In contrast to other solutions to DMARC report monitoring that pursue elaborate web dashboards designed to guide an organization through policy rollouts and infrastructure changes, this utility is intended to fill the gap for low-volume senders with already aligned infrastructure that just need to do the minimum due diligence of being alerted to unexpected problems.

Intended to be scheduled as a daily job, this uses [parsedmarc] to read DMARC reports from a specified IMAP folder and then move them to an archive in the same mailbox. If any reports indicate a problem, a notification is sent via Matrix.

Example notification:

> <details>
>   <summary>⛔ 1 message failed</summary>
>   <table>
>     <thead>
>       <tr><th>Count</th><th>Sender</th><th>SPF</th><th>DKIM</th><th>DMARC</th><th>Reporter</th></tr>
>     </thead>
>     <tbody>
>       <tr>
>         <td>1</td>
>         <td>IP: 192.0.2.1<br />rDNS: example.com<br />Envelope: example.com<br />Header: example.com</td>
>         <td>⛔<br />Aligned: No <br />example.com: pass</td>
>         <td>⛔<br />Aligned: No <br />example.com: pass</td>
>         <td>⛔<br />Aligned: No</td>
>         <td>Example</td>
>       </tr>
>     </tbody>
>   </table>
> </details>
> <details>
>   <summary>✅ 12 messages passed</summary>
>   <table>
>     <thead>
>       <tr><th>Count</th><th>Sender</th><th>SPF</th><th>DKIM</th><th>DMARC</th><th>Reporter</th></tr>
>     </thead>
>     <tbody>
>       <tr>
>         <td>6</td>
>         <td>IP: 192.0.2.2<br />rDNS: example.com<br />Envelope: example.com <br />Header: example.com</td>
>         <td>✅<br />Aligned: Yes <br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes<br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes</td>
>         <td>Example</td>
>       </tr>
>       <tr>
>         <td>3</td>
>         <td>IP: 192.0.2.3<br />rDNS: example.com<br />Envelope: example.com <br />Header: example.com</td>
>         <td>✅<br />Aligned: Yes <br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes<br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes</td>
>         <td>Example</td>
>       </tr>
>       <tr>
>         <td>2</td>
>         <td>IP: 192.0.2.3<br />rDNS: example.com<br />Envelope: example.com <br />Header: example.com</td>
>         <td>✅<br />Aligned: Yes <br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes<br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes</td>
>         <td>Example</td>
>       </tr>
>       <tr>
>         <td>1</td>
>         <td>IP: 192.0.2.4<br />rDNS: example.com <br />Envelope: example.com<br />Header: example.com</td>
>         <td>✅<br />Aligned: Yes <br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes<br />example.com: pass</td>
>         <td>✅<br />Aligned: Yes</td>
>         <td>Example</td>
>       </tr>
>     </tbody>
>   </table>
> </details>

[DMARC]: https://en.wikipedia.org/wiki/DMARC
[Matrix]: https://matrix.org/
[parsedmarc]: https://github.com/domainaware/parsedmarc
