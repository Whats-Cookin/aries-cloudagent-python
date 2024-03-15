from unittest import IsolatedAsyncioTestCase
from aries_cloudagent.tests import mock

from .......core.in_memory import InMemoryProfile
from .......ledger.base import BaseLedger
from .......ledger.multiple_ledger.ledger_requests_executor import (
    IndyLedgerRequestsExecutor,
)

from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.storage.askar import AskarProfile

from .......cache.in_memory import InMemoryCache
from .......cache.base import BaseCache
from .......indy.holder import IndyHolder
from .......anoncreds.issuer import AnonCredsIssuer
from ....models.detail.vc_di import V20CredExRecordVCDI
from ....message_types import (
    CRED_20_PROPOSAL,
)

from ...handler import V20CredFormatError

from ..handler import VCDICredFormatHandler
from ..handler import LOGGER as VCDI_LOGGER

# setup any required test data, see "formats/indy/tests/test_handler.py"
# ...
CRED_PREVIEW_TYPE = "https://didcomm.org/issue-credential/2.0/credential-preview"
TEST_DID = "LjgpST2rjsoxYegQDRm7EL"
SCHEMA_NAME = "bc-reg"
SCHEMA_TXN = 12
SCHEMA_ID = f"{TEST_DID}:2:{SCHEMA_NAME}:1.0"
SCHEMA = {
    "ver": "1.0",
    "id": SCHEMA_ID,
    "name": SCHEMA_NAME,
    "version": "1.0",
    "attrNames": ["legalName", "jurisdictionId", "incorporationDate"],
    "seqNo": SCHEMA_TXN,
}
CRED_DEF_ID = f"{TEST_DID}:3:CL:12:tag1"
CRED_DEF = {
    "ver": "1.0",
    "id": CRED_DEF_ID,
    "schemaId": SCHEMA_TXN,
    "type": "CL",
    "tag": "tag1",
    "value": {
        "primary": {
            "n": "...",
            "s": "...",
            "r": {
                "master_secret": "...",
                "legalName": "...",
                "jurisdictionId": "...",
                "incorporationDate": "...",
            },
            "rctxt": "...",
            "z": "...",
        },
        "revocation": {
            "g": "1 ...",
            "g_dash": "1 ...",
            "h": "1 ...",
            "h0": "1 ...",
            "h1": "1 ...",
            "h2": "1 ...",
            "htilde": "1 ...",
            "h_cap": "1 ...",
            "u": "1 ...",
            "pk": "1 ...",
            "y": "1 ...",
        },
    },
}
# IC - these are the minimal unit tests required for the new VCDI format class
#      they should verify that the formatter generates and receives/handles
#      credential offers/requests/issues with the new VCDI format
#      (see "formats/indy/tests/test_handler.py" for the unit tests for the
#       existing Indy tests, these should work basically the same way)


class TestV20VCDICredFormatHandler(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # any required setup, see "formats/indy/tests/test_handler.py"
        self.session = InMemoryProfile.test_session()
        self.profile = self.session.profile
        self.context = self.profile.context
        self.askar_profile = mock.create_autospec(AskarProfile, instance=True)

        setattr(self.profile, "session", mock.MagicMock(return_value=self.session))

        # Wallet
        self.public_did_info = mock.MagicMock() 
        self.public_did_info.did = 'mockedDID'
        self.wallet = mock.MagicMock(spec=BaseWallet)
        self.wallet.get_public_did = mock.CoroutineMock(return_value=self.public_did_info)
        self.session.context.injector.bind_instance(BaseWallet, self.wallet)
        
        # Ledger
        Ledger = mock.MagicMock()
        self.ledger = Ledger()
        self.ledger.get_schema = mock.CoroutineMock(return_value=SCHEMA)
        self.ledger.get_credential_definition = mock.CoroutineMock(
            return_value=CRED_DEF
        )
        # self.ledger.get_revoc_reg_def = mock.CoroutineMock(return_value=REV_REG_DEF)
        self.ledger.__aenter__ = mock.CoroutineMock(return_value=self.ledger)
        self.ledger.credential_definition_id2schema_id = mock.CoroutineMock(
            return_value=SCHEMA_ID
        )
        self.context.injector.bind_instance(BaseLedger, self.ledger)
        self.context.injector.bind_instance(
            IndyLedgerRequestsExecutor,
            mock.MagicMock(
                get_ledger_for_identifier=mock.CoroutineMock(
                    return_value=(None, self.ledger)
                )
            ),
        )
        # Context
        self.cache = InMemoryCache()
        self.context.injector.bind_instance(BaseCache, self.cache)

        # Issuer
        self.issuer = mock.MagicMock(AnonCredsIssuer, autospec=True)
        self.issuer.profile = self.askar_profile
        self.context.injector.bind_instance(AnonCredsIssuer, self.issuer) 

        # Holder
        self.holder = mock.MagicMock(IndyHolder, autospec=True)
        self.context.injector.bind_instance(IndyHolder, self.holder)

        self.handler = VCDICredFormatHandler(self.profile)
        assert self.handler.profile

    async def test_validate_fields(self):
        # Test correct data
        self.handler.validate_fields(CRED_20_PROPOSAL, {"cred_def_id": CRED_DEF_ID})

    async def test_get_vcdi_detail_record(self):
        cred_ex_id = "dummy"
        details_vc_di = [
            V20CredExRecordVCDI(
                cred_ex_id=cred_ex_id,
                rev_reg_id="rr-id",
                cred_rev_id="0",
            ),
            V20CredExRecordVCDI(
                cred_ex_id=cred_ex_id,
                rev_reg_id="rr-id",
                cred_rev_id="1",
            ),
        ]
        await details_vc_di[0].save(self.session)
        await details_vc_di[1].save(self.session)

        with mock.patch.object(
            VCDI_LOGGER, "warning", mock.MagicMock()
        ) as mock_warning:
            assert await self.handler.get_detail_record(cred_ex_id) in details_vc_di
            mock_warning.assert_called_once()

    async def test_check_uniqueness(self):
        with mock.patch.object(
            self.handler.format.detail,
            "query_by_cred_ex_id",
            mock.CoroutineMock(),
        ) as mock_indy_query:
            mock_indy_query.return_value = []
            await self.handler._check_uniqueness("dummy-cx-id")

        with mock.patch.object(
            self.handler.format.detail,
            "query_by_cred_ex_id",
            mock.CoroutineMock(),
        ) as mock_indy_query:
            mock_indy_query.return_value = [mock.MagicMock()]
            with self.assertRaises(V20CredFormatError) as context:
                await self.handler._check_uniqueness("dummy-cx-id")
            assert "detail record already exists" in str(context.exception)

    async def test_receive_request(self):
        cred_ex_record = mock.MagicMock()
        cred_request_message = mock.MagicMock()

        await self.handler.receive_request(cred_ex_record, cred_request_message)