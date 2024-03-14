from copy import deepcopy

from time import time
import json
from unittest import IsolatedAsyncioTestCase
from aries_cloudagent.tests import mock
from marshmallow import ValidationError

from .. import handler as test_module

from .......core.in_memory import InMemoryProfile
from .......ledger.base import BaseLedger
from .......ledger.multiple_ledger.ledger_requests_executor import (
    IndyLedgerRequestsExecutor,
)
from .......multitenant.base import BaseMultitenantManager
from .......multitenant.manager import MultitenantManager
from .......cache.in_memory import InMemoryCache
from .......cache.base import BaseCache
from .......storage.record import StorageRecord
from .......messaging.credential_definitions.util import CRED_DEF_SENT_RECORD_TYPE
from .......messaging.decorators.attach_decorator import AttachDecorator
from .......indy.holder import IndyHolder
from ....models.cred_ex_record import V20CredExRecord
from ....message_types import (
    ATTACHMENT_FORMAT,
    CRED_20_PROPOSAL,
    CRED_20_OFFER,
    CRED_20_REQUEST,
    CRED_20_ISSUE,
)

from ...handler import V20CredFormatError

from ..handler import VCDICredFormatHandler
from ..handler import LOGGER as INDY_LOGGER

# setup any required test data, see "formats/indy/tests/test_handler.py"
# ...
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

# IC - these are the minimal unit tests required for the new VCDI format class
#      they should verify that the formatter generates and receives/handles
#      credential offers/requests/issues with the new VCDI format
#      (see "formats/indy/tests/test_handler.py" for the unit tests for the
#       existing Indy tests, these should work basically the same way)


class TestV20VCDICredFormatHandler(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # any required setup, see "formats/indy/tests/test_handler.py"
        pass

    async def test_validate_fields(self):
        # Test correct data
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_get_indy_detail_record(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_check_uniqueness(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_create_offer(self):
        # any required tests, see "formats/indy/tests/test_handler.py"

        cred_def_id = CRED_DEF_ID
        connection_id = "test_conn_id"
        cred_attrs = {} 
        cred_attrs[cred_def_id] = {
            "name": "Alice Smith",
            "date": "2018-05-28",
            "degree": "Maths",
            "birthdate_dateint": birth_date.strftime(birth_date_format),
            "timestamp": str(int(time.time())),
        }

        cred_preview = {
            "@type": CRED_PREVIEW_TYPE,
            "attributes": [
                {"name": n, "value": v}
                for (n, v) in cred_attrs[cred_def_id].items()
            ],
        }

        offer_request = {
            "connection_id": connection_id,
            "comment": f"Offer on cred def id {cred_def_id}",
            "auto_remove": False,
            "credential_preview": cred_preview,
            "filter": {"vc_di": {"cred_def_id": cred_def_id}},
            "trace": exchange_tracing,
        }
        # this normally is sent to  "/issue-credential/send-offer", offer_request
        # maybe this is a different unit test? 
        # this data is from the faber vc_di


    async def test_receive_offer(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_create_request(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_receive_request(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_issue_credential_revocable(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_issue_credential_non_revocable(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False
