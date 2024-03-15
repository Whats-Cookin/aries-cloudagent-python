from copy import deepcopy
from time import time
from pprint import pprint
import json
import datetime
from unittest import IsolatedAsyncioTestCase
from aries_cloudagent.tests import mock
from marshmallow import ValidationError

from .. import handler as test_module

from .......core.in_memory import InMemoryProfile
from aries_askar.store import Entry
from .......ledger.base import BaseLedger
from .......ledger.multiple_ledger.ledger_requests_executor import (
    IndyLedgerRequestsExecutor,
)
from anoncreds import (CredentialDefinition, Schema)
from aries_cloudagent.core.in_memory.profile import (
    InMemoryProfile,
    InMemoryProfileSession,
)
from aries_cloudagent.anoncreds.tests.test_issuer import (
    MockCredDefEntry
)
from aries_cloudagent.anoncreds.tests.test_revocation import (
    MockEntry
)
from aries_cloudagent.anoncreds.models.anoncreds_schema import AnonCredsSchema
from aries_cloudagent.wallet.did_info import DIDInfo
from aries_cloudagent.wallet.did_method import DIDMethod
from aries_cloudagent.wallet.key_type import KeyType
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.multitenant.askar_profile_manager import AskarAnoncredsProfile

from .......multitenant.base import BaseMultitenantManager
from .......multitenant.manager import MultitenantManager
from .......cache.in_memory import InMemoryCache
from .......cache.base import BaseCache
from .......storage.record import StorageRecord
from .......messaging.credential_definitions.util import CRED_DEF_SENT_RECORD_TYPE
from .......messaging.decorators.attach_decorator import AttachDecorator
from .......indy.holder import IndyHolder
from .......anoncreds.issuer import AnonCredsIssuer
from ....models.cred_ex_record import V20CredExRecord
from ....models.detail.vc_di import V20CredExRecordVCDI
from ....messages.cred_proposal import V20CredProposal
from ....messages.cred_format import V20CredFormat
from ....messages.cred_issue import V20CredIssue
from ....messages.inner.cred_preview import V20CredPreview, V20CredAttrSpec
from ....messages.cred_offer import V20CredOffer
from ....messages.cred_request import (
    V20CredRequest,
)
from ....message_types import (
    ATTACHMENT_FORMAT,
    CRED_20_PROPOSAL,
    CRED_20_OFFER,
    CRED_20_REQUEST,
    CRED_20_ISSUE,
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
VCDI_OFFER = {
  "data_model_versions_supported": ["1.1"],
  "binding_required": True,
  "binding_method": {
    "anoncreds_link_secret": {
      "cred_def_id": "did:key:z6MkwXG2WjeQnNxSoynSGYU8V9j3QzP3JSqhdmkHc6SaVWoT/credential-definition",
      "key_correctness_proof": {
        "c": "60171843507770917958504102404278039036988796174281696438541284652582079214253",
        "xz_cap": "400900023469108743256072274885355336141962709084226652969935435522107600403767641866557986642250948789953381467236325813004928683374400754959868285491692445832927278090790033097852417149587877419726722026566721761700435075933887479442238489760418840739085317756243731825096702840445964754580905503407657279595853688247302765869506958518535547243443119883900459477082051807720780531850060680209097116540581381255805140542502243688557659901438245153911006533243007505966285664890840952116792711431348265524313950997464604211740064744408236138147252415078665776801926622694988610673079405138412888595095384317114009670879458215449994621831576277090558194116860871831084004591888804104725587283812",
        "xr_cap": [
          [
            "master_secret",
            "941831050047940929230095013777355626377027625241162515424773922545494963725439567329755765175092230944769033516564551927427624950000032771208122579862662629523124360952381871420647425204291069208959398316329685171610509033496728632063338944247346092268149581419806197357205341315919983067998135260311320130952257308322229240257925968807439348873666407907658371707880097614163030376541084038249530692752382381334109846599980752132930164770565940421031689894229533505240787217257055422932489216234637425611721771083194993187754341908249236639353769003055621768016096315843680288058772642238739655484451822960039148484132776688624671061309448523117994250189712122090567019076448183413947759218749"
          ],
          [
            "id",
            "1565826445989110234391918340514226499332591923998383797013914634700641225742942110771278982323769379611636984830055765220777930880204333284344897671518990060803138732951706204205947397876500908581743894839306725103372298211600668114986534720610729267836276269485853786168559360284378779631909230470574115521717934956105903576819301536682330599591454464442404198488354100370333092197858655675978275924876829120526787463174850379996431768606158447936578223369136811725842815442398813120970011763867298539388291179956691170973828303812700794333126974442426901974767724592589950874446636136061768165666955415635101520352028711885900513978605823832971595668489853322020411557332951701776946935249822"
          ],
          [
            "name",
            "1001220313804601353045135153406373664355109046844693939071441527037334538033227981124252053846577132503604293944629072464183043697505024886197778693226062959255971329455894813129320710070050567926337705926081793401669442889711172118463499796336430438380978686673725134855270235774630514339402940350127670327787742032197722378846494502145724590829303867325238114430957314651304145709903435261184775145704059956160959126743161341532643442279607896382417869923211653887995593725846828748395253289917165151663927894321598035126258821368270191059245235858595192494451465156157417194844088912102344983060924144927338046787350568607553785796159703550500853172679206794578973059013264280792870547327809"
          ],
          [
            "age",
            "1412450931347724354333701007255424233236894801323309278892438382405541601692044745877872269610698527710217979045180027813738248970288719523659096203236108176000319497416959968016822213963293282490269447263298026951268059597975129774957101307004747229329693219271062805006825722748724686178357524799392206731954678773923706677805386679418338956483675249068554897485273445485612322468116078198555715372507074988096487061749879180499320866151692802506090962442796720089236600661096997227974428519236080065511985612926681659088956131584709150284711954923115212026683420245627958138303985539225850433088386723418996124660495648368763366701150694446657644624869409402824715981866111857845577363462146"
          ],
          [
            "height",
            "1165964812541525135244876217097498170198341440948420540840033012473404101266667447773358199131984075013032493459641160472919705655354275028545906538050792197856824730602930168183517558816522047881376719673563659603265685245057561330458611625129283713121986990741844118717933866073443449785903542285073637115064002631703478778949020265493974065504570312972877916886087558591057783524102316457701137879165948068264571207236798004333543043781535400003731474308760314262396582070434767382649149625600216068028008587495401678153241193030013877670326850575729519668786697527176759292175776604082446432920635961955328468783534910392468904032108773652299651678236838766886834036039151956227925152516526"
          ],
          [
            "sex",
            "1529205896442288430287151083759310432774768088442639950805979341469233816025321246813154760544542196162003665742053836144231098246189162293474679661869990026945596168347832313921238104983068282939318264142479059584286752886921240876389268903114981897700548588530033017944246918241145394448542215583655396405779090527682120929760466887175023368031907825102565889441924594179816829897813181022985312812796544115996143025576000873684206423259216058711593411535047188201556948017289231003468783241986670238444087552119190397920742685813159846444548412718641870244372245170085299243456828685284245999151318010899055040515512461880283742006258864468278122178619068187082295594786143040047003598829583"
          ]
        ]
      },
      "nonce": "67015657521700289393067"
    },
    "didcomm_signed_attachment": {
      "algs_supported": ["EdDSA"],
      "did_methods_supported": ["key"],
      "nonce": "b19439b0-4dc9-4c28-b796-99d17034fb5c"
    }
  },
  "credential": {
    "@context": [
      "https://www.w3.org/2018/credentials/v1",
      "https://w3id.org/security/data-integrity/v2",
      {
        "@vocab": "https://www.w3.org/ns/credentials/issuer-dependent#"
      }
    ],
    "type": ["VerifiableCredential"],
    "issuer": "did:key:z6MkwXG2WjeQnNxSoynSGYU8V9j3QzP3JSqhdmkHc6SaVWoT",
    "credentialSubject": {
      "height": 175,
      "age": 28,
      "name": "Alex",
      "sex": "male"
    },
    "issuanceDate": "2024-01-10T04:44:29.563418Z"
  }
}
VCDI_CRED_REQ = {
  "data_model_version": "1.1",
  "binding_proof": {
    "anoncreds_link_secret": {
      "entropy": "entropy",
      "cred_def_id": "did:key:z6MkwXG2WjeQnNxSoynSGYU8V9j3QzP3JSqhdmkHc6SaVWoT/credential-definition",
      "blinded_ms": {
        "u": "14895943100494688932538229133861409561073492709308729179809631001894673446486623547482963545354011800303411800173266138196195959202789988521947907381607876767237432760205977569148724150226426116520817428665167989038697199662225676576739237104393957091999777564892355494377293823788760696647155555317383770319030865988559933185227421268886076307286905983003453133473349532890920355813358773762679171310108114247631384148019383302172041101495061368753361231504607532703024124447181461157113498238349000301538116852924084929493440189256633286874670166386301197952784169776587391156626192665844587054515577941820856959169",
        "ur": "1 22D60DABB059FA83EAAA69F8230DC7F1F4FFCE05741905D0BD3474390976EC51 1 06E985C85E745AC1768CCBED5D1BF1305BF227D3E203D855F84F715DB60DB890 2 095E45DDF417D05FB10933FFC63D474548B7FFFF7888802F07FFFFFF7D07A8A8",
        "hidden_attributes": ["master_secret"],
        "committed_attributes": {}
      },
      "blinded_ms_correctness_proof": {
        "c": "46303859065320631890592727985568678695818030278813543246555368587544563701817",
        "v_dash_cap": "874236075806607035680206611139535961396526644068179111368994839924822157529393233945929940912776608661764193053226966197674833199292392646999902126745003950887627571877398891831746998813248233354056622425582445060383511309075655063157643125447604680494679503994520293048436880298916220850498808212303121868086978756997741103393205099680183226683478316967685557710756238506433819993679884750562123712515903461189421531947085820083340192589555311852117291176162111332784739332693220678060381437994413846100529769256386456681397757513115143063943829104605413222329681325030521213686552670530020786687651113552692528259608248845895701422462814252119213774349181049866432560469115615348875179750725191435030292798673852740",
        "m_caps": {
          "master_secret": "112055588005440869398357016098075106043046944772150383754402915741795446648725040017815006204022281897994753535216619853326071574777841471732022846445972964269970627743658295526"
        },
        "r_caps": {}
      },
      "nonce": "873772755980407430956688"
    },
    "didcomm_signed_attachment": {
      "attachment_id": "6c2781e0-64fe-4330-828b-b2cf157cf1fe"
    }
  }
}
VCDI_CRED = {
  "credential": {
    "@context": [
      "https://www.w3.org/2018/credentials/v1",
      "https://w3id.org/security/data-integrity/v2",
      {
        "@vocab": "https://www.w3.org/ns/credentials/issuer-dependent#"
      }
    ],
    "type": ["VerifiableCredential"],
    "issuer": "did:key:z6MkwXG2WjeQnNxSoynSGYU8V9j3QzP3JSqhdmkHc6SaVWoT",
    "credentialSubject": {
      "height": 175,
      "id": "did:key:z6MkkwiqX7BvkBbi37aNx2vJkCEYSKgHd2Jcgh4AUhi4YY1u",
      "age": 28,
      "name": "Alex",
      "sex": "male"
    },
    "proof": [
      {
        "type": "DataIntegrityProof",
        "cryptosuite": "anoncredsvc-2023",
        "proofValue": "ueyJjcmVkX2RlZl9pZCI6ImRpZDprZXk6ejZNa3dYRzJXamVRbk54U295blNHWVU4VjlqM1F6UDNKU3FoZG1rSGM2U2FWV29UL2NyZWRlbnRpYWwtZGVmaW5pdGlvbiIsInJldl9yZWciOnsiYWNjdW0iOiIxIDFGMkQyMDVBMjQzNURFMzYyNTA3RUIyMEMxQzFGMzdCRkMxNURFRTY3Nzg0MkUyN0E2M0IyNjZGOUVERkZCNjggMSAyNDk1OUUwNkFBQjQ3QzhFQkM2MkI3OEZCMjgyMzJCMDA4Q0RBMEMzOURDN0JDRUI2QjA3M0EyRTI2NEYzRkU2IDEgMUUyQjgxNDA4QjE2RDdDODQyREU3NTg0QjY5MEVFMTU3MDI3MzEzOUZBNjdFNkZBMkNEQUIyMTc1OENDODAzOSAxIDA3OUI2NUZERDZFNDlFRDE0NDlEQUY2NEU5NzIyQUZENEY5RjQxMDY4NTMyNkUxMjJBNjE1OUY4MTY1NjdFMzEgMiAwOTVFNDVEREY0MTdEMDVGQjEwOTMzRkZDNjNENDc0NTQ4QjdGRkZGNzg4ODgwMkYwN0ZGRkZGRjdEMDdBOEE4IDEgMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMCJ9LCJyZXZfcmVnX2lkIjoiZGlkOmtleTp6Nk1rd1hHMldqZVFuTnhTb3luU0dZVThWOWozUXpQM0pTcWhkbWtIYzZTYVZXb1QvcmV2b2NhdGlvbi1yZWdpc3RyeSIsInNjaGVtYV9pZCI6ImRpZDprZXk6ejZNa3dYRzJXamVRbk54U295blNHWVU4VjlqM1F6UDNKU3FoZG1rSGM2U2FWV29UL3NjaGVtYSIsInNpZ25hdHVyZSI6eyJwX2NyZWRlbnRpYWwiOnsiYSI6IjUxNTQzMzM4MDk5ODcwMTYzOTM3Njk0MzI1MjQwNjI0MTczNzM2NTcwMTQ1MDUyMjU3NTgyOTkzMjYyNDYzNzIzNDQzNzg4NDQzMjAzMjE4MTY1NjA3MTMwMzc1NDE0Njg1NjMzNTg0MDIwMDI1MTQ3ODgzMzcxNTQ1ODk4ODE1Njk3MzQ0OTQ4NjY5Nzc0MDUyMDMyMDYzODY4ODc2Njg0Njg5OTA1NDg4OTMzMjI3Mjk0NTM3NTg4NjQ1MTQ5OTkzNzY2MTYyNTY2NzEwMDU4NDE5NzM0NjQ3Nzg3MjcwNjc3Mjg1NjMxMzIwNDUzMTI2NjAwMzkxNjg1MDI4NzY3NzIxNzU3NjU1OTM0ODI2MzY5NjQwNTUwNzAyNzE0NDk4NzIyNzQyNzE5OTE3NDczNzg4NTgwMDY1MDIzMTU5NTYwOTY3OTQ3NTY0MjE2OTQxNTk3OTc0NzQ5ODg1ODk0MDQ5NDAyMDQ1NjQzNjMwMzI1MTkxMzk1MTE1MTcyMzM0NDk0OTE1MTc2ODQyMTc5NDIyODk4NjAzNDk2NTExNzU2NzgxOTc1NTc5OTg2MzE0OTY3Mjk3ODM2OTk3MzMzMjg2ODY0NDU1OTc2MTM1MDg3MDg0NjExNTgwMDczMjk4MTA5NDM3OTY1MTAxNDU1MDU4OTI2NjE4MjE1NzcyMzc2NDEwNjAwMzc2NjYwMTQ2OTQxMzU0ODU3MDQ3MTA0NTYwOTg4NDQ1MDY4NDQyNzMyOTUyMzM3MzQ5NzkyMDcxODY5NTg2ODM0NDQ3OTc3MjUyMDk4MjQ0MTI2MzEwMDgzNjUwOTI0IiwiZSI6IjI1OTM0NDcyMzA1NTA2MjA1OTkwNzAyNTQ5MTQ4MDY5NzU3MTkzODI3Nzg4OTUxNTE1MjMwNjI0OTcyODU4MzEwNTY2NTgwMDcxMzMwNjc1OTE0OTk4MTY5MDU1OTE5Mzk4NzE0MzAxMjM2NzkxMzIwNjI5OTMyMzg5OTY5Njk0MjIxMzIzNTk1Njc0MjkyOTc0MTI5NzA4NTA1NTU4MzQxMjQ2ODE0NjEyNzkzMjc2NTI2OSIsIm1fMiI6IjkyOTIyOTY1MjQxMzk0MjA0NDk4NzQ5NzM5NjI1NjQ1OTk5OTYwOTk0OTcyMjg1NDczNjU5NzExODk3NjUyMTEzNDUzMDYyMDYxMDY5IiwidiI6IjY2ODI1MTIyNDQzMzc0MjYxNjYwMzYzMTMwMzE5NjU2MzYyMjU4MTY2MzU2MzQ5ODQ5NDQ4Nzk5NDA0MjUyMDM5MDQyMDYzNzQwNDUxNDMyMDg3NDE3ODIwMjI0NTMwMDY1ODg3NjAyMzkzOTM5NDg2NjAxMjQzNzU1OTM3NjUzMTczNzc0NTE1MDE5MjkwNzQ4MTM1NzY1NDUxODE5Mzc4NTMwNTA4NDUwNjYyODk5MDE1NDQwNzMzNjYwNDY4MjM1MTc2NDgzOTk3MDYzNzY3MTA1MTU0NDkyMjk5Nzg0OTQ4NjI2NDg5MTAzMzk1NDI5MTA2NDExMzg1NDA1NjYyNTY3OTU1MjAxOTMyMDE2MDc2NDcyMzA3MzQ4NDY0MzczMzg5MDQ1OTEwMDUxNDc3NzI3NDE3ODU1MzYyOTk5NzgyMTAyMzM3NDE0NDQ1MTk3MDkxMDc4ODQ2MTI1OTE5NDc1NDgyOTY4MjEzNDg4Mzk0NjQ5MjIyMjY5MDI3NzI5MzI4NDI3OTU4OTE0ODMwODQzNDQ3NjIwNDA2MjYxMDk0NjUwNzM0MDA0MTIwMzMzNzk2NjY3ODQ3Njk2MDc1OTI3NDU4NTgyMjcwMDY3NjQ0NzA3MDkxMzU4OTQ4ODQ4MDY3NTM4MzE3MzE1MDg0MTg5ODAxODA4OTM5NjMwMjE5OTQzMzA3MjExODg5NTQ4MjIyMzUwMDYwMzkzNjU2MDYyMzYzODQ5OTQzMzc2NDk1MTg4ODI0NDk4OTMyNTEwNjYwMzU2NDI5NDQwMzA4MTk1NTA0OTM2NTA1OTk3MDczMzIxNzQ5NDcyMzY1NTA3MzYyOTY1Mzk1NDg1MDM2Njg1MTI0MjE2MDU3MTIxMjk2NTc3NTQ5MDEzNzIxMDA4ODc3MzAxMDE4OTg3OTIyNjI0Mzk2ODI0NjQwNTUzMzU2NDcyODg1NzU2MTc2ODYyNjAwNzA1MzM2MDg0ODQ3OTg1MDYzMDk5MDEwNDY2OTI4NjEwMTQ4MTMzMzYwMDkxNjI0ODY1NDkwMDY0MDQ3OTE5NjkxNjcxMDE1MzA0MjQzNDM0MTEwOTk1MTY2OTUyMDQifSwicl9jcmVkZW50aWFsIjp7ImMiOiIwMjNCMjE4M0VERUI1OUI4MENCRDNCNEIwRDE5QTZENjlFNUI2RDRDRTlDOEJGNTBGOTVCOEZDQjVBMjI4MzVDIiwiZ19pIjoiMSAxMUIwMzU5NDEzOEQ5N0UyNzExQjMxRUU1RkNDQkRENDgzNjkyQzg2N0Y3QUZCMzY5QjEyNjA2NkJCMDZEOTg1IDEgMDk3MDYxNDkyNTNEM0ZERTIwNDQ2RTQ3MzAxNUI1Q0Q3MTFGMkRCRTE3QUMyQTYwNEU1RUU3QUFGMUNGNzRGMyAyIDA5NUU0NURERjQxN0QwNUZCMTA5MzNGRkM2M0Q0NzQ1NDhCN0ZGRkY3ODg4ODAyRjA3RkZGRkZGN0QwN0E4QTgiLCJpIjo5LCJtMiI6IjEzQkY5MjRBRTI4QUFDQ0JCQzlGRjk5MURFNUEwNjU0NDQ2RDE5OEJFNkYzN0EzQjk0NEE2OUU1MzFDODdCQ0MiLCJzaWdtYSI6IjEgMTcxMEI4NjU1N0FDMDM0MURCMjJBNjFFQzAzMDdFODA2QUVDN0I3OTY0OTA1QkJDQTc1REMyNDNBRDYwMDgzQSAxIDFGNjk2QTJFRDRDQTM1RDQ5RjUyN0NGRERBQjVDM0E5QTA3RURFNkRFNEE4RTYwMkYxNTZGNUNENjQ4NjJDM0YgMiAwOTVFNDVEREY0MTdEMDVGQjEwOTMzRkZDNjNENDc0NTQ4QjdGRkZGNzg4ODgwMkYwN0ZGRkZGRjdEMDdBOEE4IiwidnJfcHJpbWVfcHJpbWUiOiIwQjA5NjA2NjdGOTI3NEY3RDJCM0M1MkVFOTg2MzQzMEQ1OEZDN0FBNTEwNEFBQkY0ODJBRDRFQjMyMDUwQTRBIiwid2l0bmVzc19zaWduYXR1cmUiOnsiZ19pIjoiMSAxMUIwMzU5NDEzOEQ5N0UyNzExQjMxRUU1RkNDQkRENDgzNjkyQzg2N0Y3QUZCMzY5QjEyNjA2NkJCMDZEOTg1IDEgMDk3MDYxNDkyNTNEM0ZERTIwNDQ2RTQ3MzAxNUI1Q0Q3MTFGMkRCRTE3QUMyQTYwNEU1RUU3QUFGMUNGNzRGMyAyIDA5NUU0NURERjQxN0QwNUZCMTA5MzNGRkM2M0Q0NzQ1NDhCN0ZGRkY3ODg4ODAyRjA3RkZGRkZGN0QwN0E4QTgiLCJzaWdtYV9pIjoiMSAwM0JBREM1MEIxREMzODA3MzNBQzZEQThGN0RCNUFERjc1NDNBM0E5RTQ4MDhBOUUzMjVCREFEQTc0NUI2M0IyIDEgMDhERkUyQUNCMDI3OEU3NkFDRjg3Nzk1OEIxQUQ4NjQ5QzdBNTYyNTBGNjIxMDgwM0Y4RDY1MzczODQ2NzU4RSAxIDFBNDE5QTlGQUZENTg0NkE4Nzc1QTlEQzA5MjdCMTUzM0U5QjA3RjJBRDRFMzUxREY1M0FCRjkwQkY1NzdDMjIgMSAxQTlBQTc5MTRBNERERERDNURDOEIzNkRDNDg5NURCQzZBMjZDNjZGODFCQjlFM0NFMEVCMUJCRTg4QThCNjFDIDIgMDk1RTQ1RERGNDE3RDA1RkIxMDkzM0ZGQzYzRDQ3NDU0OEI3RkZGRjc4ODg4MDJGMDdGRkZGRkY3RDA3QThBOCAxIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAiLCJ1X2kiOiIxIDBFNTM5N0Q4NUUwMkI5MTdDMjcxQzc4NTg5RDYxRkUwQjdERkI5QTUwRTdDMTEyQTM2MUI2RjQyMzc5Q0E4QzYgMSAxODBGOTFDMjUzNzk3MzU4M0FGRDM5ODUxNDNGNTc3NzYwRUI5QTJCNkRFMDY3NjM4NjQ2QkI3RDlDNEVDNjZFIDEgMTQ1OTYyODM5NzY3ODMzMzRBNEU1RTJBNjA5RTM2QzE1QTlBQUY2RDA0N0Y1QTYyMjc2NkIwODBCRjk3RDUyQSAxIDBBN0ExQzdEQTIyOTY5OTczQ0U5MjNFRjNBMzhDODlDMzU2Njg1MzFFRDY1OTE0MEJEMTlEMEY2RkQ2QkM4QzYgMiAwOTVFNDVEREY0MTdEMDVGQjEwOTMzRkZDNjNENDc0NTQ4QjdGRkZGNzg4ODgwMkYwN0ZGRkZGRjdEMDdBOEE4IDEgMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMCJ9fX0sInNpZ25hdHVyZV9jb3JyZWN0bmVzc19wcm9vZiI6eyJjIjoiMTA0MDEwNTA1NDczMTExMDg2MjAyMDA4ODk5NzA4MzQzNjg1OTE4MzM0ODUwMzEyMDQ4Mzg4MTk4MDc4Nzk3ODEzMTE1ODM3NTA2NDAwIiwic2UiOiI0MzU5MTgwNDQ3OTIyODc0NDk3OTU0NDIzNjMxMTAzNTQ0OTQwOTgzMjU5NzI3MjMyMjgyOTI3MjQyMzQ1NzUyODcwMjk1MTczMDc0MTM0NDU4NTU5MDIwNjI0Mzk3OTA4OTAwNDcwMzM1NzAyNjMxNjY0Njg2MjAyODQ0MzYyOTAyNjI3MjMwNDU4MjgyNDAxNjg0NTA1Mzc2NzAyMTEyMDUwNzc5MzQ1NzA2ODA2MTU2OTY4MTkzNjA4NDE2NTI1MTUwNTUxNjc3NDIwNzMyMTExMzQwMzI1MDM2MjkyMjc0MTMwMTg1ODc4MTQwNDcxNTkyNTg0ODYwNjc1MzA5ODM4MTAyMjk1MTY4NTcwOTQzODc4MTUwNzE0Njc1NDk2MTk4MDEzOTczMjk1MDYwMzU1MjEyMDQxMjA2Mzg1OTYyODEyODkyMDA0MDQ2MjgyNDIyNDAzMzk3MzAwNTc1MzQ1ODA1ODYzNDYxMDk2MDg5ODMzMjQ4NTc3OTc5MTMyMjUwNzYxMjEyODg1Mjc3MjA4MTYyMzAyMzI0MTcxMzcxNDczNzIyNDQ2MTYzMjczMDg0NDIwMDIxNDA0MjYwMjIwNTAyMTI4MzEwMjY4NDQ1ODA1OTQ5MDIwODU4OTA2NTA3NjcxNjgyNjYxNjgyMTQzMTAzNjI5MDQ5NDk3NTE0MTI5MDQwNzU4NzU4OTgxOTg4MDg5NDY5MTUzMzAxMzU3MTQ1NTcwNDUzNzUyODExNzc2NTAxMjIzMDk1MjIzOTMzMjAzNzA0NjY2NzA2NjM2Njk0MTI1ODcyNjM2OTc1MzM5MiJ9LCJ3aXRuZXNzIjp7Im9tZWdhIjoiMSAxNTNDM0RDRjRGMDFGNDkwMDNBQUM1MjY2RUU5QzczNTk3RjMxRTFCQ0QwRDVCQUMyRjBFNDFDMkI3MUJGMUM5IDEgMEVDM0QwRTMyODIyOTI4NDI4QUU1Q0U1NTg0NTVDMzZEQjIzNjJCNTVFMEUyN0QxQjE2QkYwOTczNzM1OTMwRCAxIDBCNkI2MzlGQUM3NEY4QjRBMDkwNDE4NjUyMzdGMTlDRjg3MjcyRDE0QUVENkE5QTMwRTkzMUFFNEQxQzNCNDkgMSAxQUE1NkJFNjhEMUVDRTc1MzgxNDQ5RjMwQzExQUMzQzk1NjY0RTNBQjNFMkI4Q0U5MjFFMjc1RTVDQjQ1ODlCIDIgMDk1RTQ1RERGNDE3RDA1RkIxMDkzM0ZGQzYzRDQ3NDU0OEI3RkZGRjc4ODg4MDJGMDdGRkZGRkY3RDA3QThBOCAxIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAifX0"
      },
      {
        "type": "DataIntegrityProof",
        "created": "2024-01-10T04:55:06Z",
        "verificationMethod": "did:key:z6MkwXG2WjeQnNxSoynSGYU8V9j3QzP3JSqhdmkHc6SaVWoT#z6MkwXG2WjeQnNxSoynSGYU8V9j3QzP3JSqhdmkHc6SaVWoT",
        "cryptosuite": "eddsa-rdfc-2022",
        "proofPurpose": "assertionMethod",
        "proofValue": "z2XDK7svzSHbdQM3t1FhQiTWPhSosUiHL4AEPLhAM82at8E7EBvz3BLwJDFzWdfhcJ4RiAnoFTRCkh9H7G5n6e2mm"
      }
    ],
    "issuanceDate": "2024-01-10T04:44:29.563418Z"
  }
}

# IC - these are the minimal unit tests required for the new VCDI format class
#      they should verify that the formatter generates and receives/handles
#      credential offers/requests/issues with the new VCDI format
#      (see "formats/indy/tests/test_handler.py" for the unit tests for the
#       existing Indy tests, these should work basically the same way)


class TestV20VCDICredFormatHandler(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # any required setup, see "formats/indy/tests/test_handler.py"
        self.session = InMemoryProfile.test_session(profile_class=AskarAnoncredsProfile)
        self.profile = self.session.profile
        self.context = self.session.profile.context

        setattr(self.profile, "session", mock.MagicMock(return_value=self.session))

        # Issuer
        self.patcher = mock.patch('aries_cloudagent.protocols.issue_credential.v2_0.formats.vc_di.handler.AnonCredsIssuer', autospec=True)
        self.MockAnonCredsIssuer = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.issuer = mock.create_autospec(AnonCredsIssuer, instance=True)
        self.MockAnonCredsIssuer.return_value = self.issuer

        self.issuer.profile = self.profile


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
        self.ledger.get_revoc_reg_def = mock.CoroutineMock(return_value=REV_REG_DEF)
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


        # Holder
        self.holder = mock.MagicMock(IndyHolder, autospec=True)
        self.context.injector.bind_instance(IndyHolder, self.holder)

        self.handler = VCDICredFormatHandler(self.profile)
        assert self.handler.profile

    async def test_validate_fields(self):
        # Test correct data
        self.handler.validate_fields(CRED_20_PROPOSAL, {"cred_def_id": CRED_DEF_ID})
        self.handler.validate_fields(CRED_20_OFFER, VCDI_OFFER) 
        self.handler.validate_fields(CRED_20_REQUEST, VCDI_CRED_REQ)
        self.handler.validate_fields(CRED_20_ISSUE, VCDI_CRED)
        
        
        # test incorrect proposal
        with self.assertRaises(ValidationError):
            self.handler.validate_fields(
                CRED_20_PROPOSAL, {"some_random_key": "some_random_value"}
            )

        # test incorrect offer
        with self.assertRaises(ValidationError):
            offer = VCDI_OFFER.copy()
            offer.pop("nonce")
            self.handler.validate_fields(CRED_20_OFFER, offer)

        # test incorrect request
        with self.assertRaises(ValidationError):
            req = VCDI_CRED_REQ.copy()
            req.pop("nonce")
            self.handler.validate_fields(CRED_20_REQUEST, req)

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

    async def test_create_offer(self, mock_session_handle):

        age = 24
        d = datetime.date.today()
        birth_date = datetime.date(d.year - age, d.month, d.day)
        birth_date_format = "%Y%m%d"

        cred_def_id = CRED_DEF_ID
        connection_id = "test_conn_id"
        cred_attrs = {} 
        cred_attrs[cred_def_id] = {
            "legalName": VCDI_CRED["values"]["legalName"],
            "incorporationDate": VCDI_CRED["values"]["incorporationDate"],
            "jurisdictionId": VCDI_CRED["values"]["jurisdictionId"],
        }

        attributes = [V20CredAttrSpec(name=n, value=v) for n, v in cred_attrs[cred_def_id].items()]

        cred_preview = V20CredPreview(attributes=attributes)

        cred_proposal = V20CredProposal(
            credential_preview=cred_preview,
            formats=[
                V20CredFormat(
                    attach_id="0",
                    format_=ATTACHMENT_FORMAT[CRED_20_PROPOSAL][
                        V20CredFormat.Format.VC_DI.api
                    ],
                )
            ],
            filters_attach=[
                AttachDecorator.data_base64({"cred_def_id": CRED_DEF_ID}, ident="0")
            ],
        )

        schema_id_parts = SCHEMA_ID.split(":")
        cred_def_record = StorageRecord(
            CRED_DEF_SENT_RECORD_TYPE,
            CRED_DEF_ID,
            {
                "schema_id": SCHEMA_ID,
                "schema_issuer_did": schema_id_parts[0],
                "schema_name": schema_id_parts[-2],
                "schema_version": schema_id_parts[-1],
                "issuer_did": TEST_DID,
                "cred_def_id": CRED_DEF_ID,
                "epoch": str(int(time())),
            },
        )
        await self.session.storage.add_record(cred_def_record)


        original_create_credential_offer = self.issuer.create_credential_offer
        self.issuer.create_credential_offer = mock.CoroutineMock(
            return_value=json.dumps(VCDI_OFFER)
        )


        (cred_format, attachment) = await self.handler.create_offer(cred_proposal)

        # this enforces the data format needed for alice-faber demo
        assert attachment.content == VCDI_OFFER 

        self.issuer.create_credential_offer.assert_called_once()

        # assert identifier match
        assert cred_format.attach_id == self.handler.format.api == attachment.ident

        # assert data is encoded as base64
        assert attachment.data.base64

        self.issuer.create_credential_offer = original_create_credential_offer


    async def test_receive_offer(self):
        holder_did = "did"

        cred_offer = V20CredOffer(
            formats=[
                V20CredFormat(
                    attach_id="0",
                    format_=ATTACHMENT_FORMAT[CRED_20_OFFER][
                        V20CredFormat.Format.VC_DI.api
                    ],
                )
            ],
            offers_attach=[AttachDecorator.data_base64(VCDI_OFFER, ident="0")],
        )
        cred_ex_record = V20CredExRecord(
            cred_ex_id="dummy-id",
            state=V20CredExRecord.STATE_OFFER_RECEIVED,
            cred_offer=cred_offer.serialize(),
        )

        cred_def = {"cred": "def"}
        self.ledger.get_credential_definition = mock.CoroutineMock(
            return_value=cred_def
        )

        cred_req_meta = {}
        self.holder.create_credential_request = mock.CoroutineMock(
            return_value=(json.dumps(VCDI_CRED_REQ), json.dumps(cred_req_meta))
        )

        (cred_format, attachment) = await self.handler.create_request(
            cred_ex_record, {"holder_did": holder_did}
        )

        self.holder.create_credential_request.assert_called_once_with(
            VCDI_OFFER, cred_def, holder_did
        )

        # assert identifier match
        assert cred_format.attach_id == self.handler.format.api == attachment.ident

        # assert content of attachment is proposal data
        assert attachment.content == VCDI_CRED_REQ

        # assert data is encoded as base64
        assert attachment.data.base64

        # cover case with cache (change ID to prevent already exists error)
        cred_ex_record._id = "dummy-id2"
        await self.handler.create_request(cred_ex_record, {"holder_did": holder_did})

        # cover case with no cache in injection context
        self.context.injector.clear_binding(BaseCache)
        cred_ex_record._id = "dummy-id3"
        self.context.injector.bind_instance(
            BaseMultitenantManager,
            mock.MagicMock(MultitenantManager, autospec=True),
        )
        with mock.patch.object(
            IndyLedgerRequestsExecutor,
            "get_ledger_for_identifier",
            mock.CoroutineMock(return_value=(None, self.ledger)),
        ):
            await self.handler.create_request(
                cred_ex_record, {"holder_did": holder_did}
            )
        cred_ex_record = mock.MagicMock()
        cred_offer_message = mock.MagicMock()
        await self.handler.receive_offer(cred_ex_record, cred_offer_message)


    async def test_create_request(self):
        holder_did = "did"

        cred_offer = V20CredOffer(
            formats=[
                V20CredFormat(
                    attach_id="0",
                    format_=ATTACHMENT_FORMAT[CRED_20_OFFER][
                        V20CredFormat.Format.VC_DI.api
                    ],
                )
            ],
            offers_attach=[AttachDecorator.data_base64(VCDI_OFFER, ident="0")],
        )
        cred_ex_record = V20CredExRecord(
            cred_ex_id="dummy-id",
            state=V20CredExRecord.STATE_OFFER_RECEIVED,
            cred_offer=cred_offer.serialize(),
        )

        cred_def = {"cred": "def"}
        self.ledger.get_credential_definition = mock.CoroutineMock(
            return_value=cred_def
        )

        cred_req_meta = {}
        self.holder.create_credential_request = mock.CoroutineMock(
            return_value=(json.dumps(VCDI_CRED_REQ), json.dumps(cred_req_meta))
        )

        (cred_format, attachment) = await self.handler.create_request(
            cred_ex_record, {"holder_did": holder_did}
        )

        self.holder.create_credential_request.assert_called_once_with(
            VCDI_OFFER, cred_def, holder_did
        )

        # assert identifier match
        assert cred_format.attach_id == self.handler.format.api == attachment.ident

        # assert content of attachment is proposal data
        assert attachment.content == VCDI_CRED_REQ

        # assert data is encoded as base64
        assert attachment.data.base64

        # cover case with cache (change ID to prevent already exists error)
        cred_ex_record._id = "dummy-id2"
        await self.handler.create_request(cred_ex_record, {"holder_did": holder_did})

        # cover case with no cache in injection context
        self.context.injector.clear_binding(BaseCache)
        cred_ex_record._id = "dummy-id3"
        self.context.injector.bind_instance(
            BaseMultitenantManager,
            mock.MagicMock(MultitenantManager, autospec=True),
        )
        with mock.patch.object(
            IndyLedgerRequestsExecutor,
            "get_ledger_for_identifier",
            mock.CoroutineMock(return_value=(None, self.ledger)),
        ):
            await self.handler.create_request(
                cred_ex_record, {"holder_did": holder_did}
            )

    async def test_receive_request(self):
        cred_ex_record = mock.MagicMock()
        cred_request_message = mock.MagicMock()

        await self.handler.receive_request(cred_ex_record, cred_request_message)

    async def test_issue_credential_revocable(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False

    async def test_issue_credential_non_revocable(self):
        # any required tests, see "formats/indy/tests/test_handler.py"
        assert False
