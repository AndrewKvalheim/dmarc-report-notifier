FROM python:3-alpine

# System dependencies
RUN apk add --no-cache poetry supercronic

WORKDIR /usr/src/app

# Application dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-cache --no-interaction --no-root

# Application
COPY README.md ./
COPY dmarc_report_notifier ./dmarc_report_notifier
RUN poetry install --no-cache --no-interaction --only-root

# Schedule
ENV SCHEDULE="@daily"
CMD supercronic <( echo "$SCHEDULE poetry run dmarc-report-notifier" )
