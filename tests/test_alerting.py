import smtplib
import services.alerting as alerting


def test_send_webhook(monkeypatch):
    payloads = []

    class DummyResponse:
        status_code = 200

    def fake_post(url, json, timeout):
        payloads.append((url, json, timeout))
        return DummyResponse()

    monkeypatch.setenv('ALERT_WEBHOOK_URL', 'http://test-webhook.local')
    monkeypatch.setattr(alerting.requests, 'post', fake_post)

    alerting.send_alert_notification('TestCity', 4.5, 4)
    assert payloads
    assert payloads[0][0] == 'http://test-webhook.local'
    assert payloads[0][1]['city'] == 'TestCity'


def test_send_email(monkeypatch):
    emails = []

    class DummySMTP:
        def __init__(self, host, port, timeout):
            pass

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def sendmail(self, from_addr, to_addrs, message):
            emails.append((from_addr, to_addrs, message))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setenv('SMTP_HOST', 'smtp.test.local')
    monkeypatch.setenv('SMTP_PORT', '587')
    monkeypatch.setenv('SMTP_USER', 'user@test.local')
    monkeypatch.setenv('SMTP_PASSWORD', 'password')
    monkeypatch.setenv('ALERT_EMAIL_TO', 'recipient@test.local')
    monkeypatch.setattr(smtplib, 'SMTP', DummySMTP)

    alerting.send_alert_notification('TestCity', 5.0, 4)
    assert emails
    assert emails[0][1] == ['recipient@test.local']
