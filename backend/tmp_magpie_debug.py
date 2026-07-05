import asyncio
import json
import httpx
from services.magpie_service import MagpieService

class DummyResp:
    def __init__(self, status_code, text, data):
        self.status_code = status_code
        self._text = text
        self._data = data

    @property
    def text(self):
        return self._text

    def json(self):
        return self._data


class SeqClient:
    def __init__(self, responses):
        self._responses = list(responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        print('post url=', url)
        print('post payload=', json)
        print('post headers=', headers)
        if not self._responses:
            raise RuntimeError('No more responses')
        return self._responses.pop(0)


def main():
    responses = [
        DummyResp(200, json.dumps({'checkout_id':'co_123','checkout_url':'https://magpie/checkout/co_123','external_id':'ext123'}), {'checkout_id':'co_123','checkout_url':'https://magpie/checkout/co_123','external_id':'ext123'}),
        DummyResp(200, json.dumps({'qr_id':'qr_123','qr_content':'https://magpie/qr/qr_123','external_id':'extqr'}), {'qr_id':'qr_123','qr_content':'https://magpie/qr/qr_123','external_id':'extqr'}),
    ]
    httpx.AsyncClient = lambda *args, **kwargs: SeqClient(responses)

    svc = MagpieService()
    svc.api_key = 'test'

    async def run():
        checkout = await svc.create_checkout(amount=100.0, description='test', external_id='ext123')
        print('checkout', checkout)
        qr = await svc.create_qr_payment(amount=111.0, description='qr', external_id='extqr')
        print('qr', qr)

    asyncio.run(run())


if __name__ == '__main__':
    main()
