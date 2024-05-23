#!/usr/bin/env python3

import asyncio
import dmarc_report_notifier


def main():
    asyncio.run(dmarc_report_notifier.main())


if __name__ == "__main__":
    main()
