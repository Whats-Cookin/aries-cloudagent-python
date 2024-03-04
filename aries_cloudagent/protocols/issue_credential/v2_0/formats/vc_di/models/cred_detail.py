"""Linked data proof verifiable options detail artifacts to attach to RFC 453 messages."""

from typing import Optional, Union

from marshmallow import INCLUDE, fields


from .......messaging.models.base import BaseModel, BaseModelSchema
from .......vc.vc_ld import CredentialSchema
from .......vc.vc_ld.models.credential import VerifiableCredential
from .cred_detail_options import VCDIDetailOptions, VCDIDetailOptionsSchema

# class LDProofVCDetail(BaseModel):
#     """Linked data proof verifiable credential detail."""

#     class Meta:
#         """LDProofVCDetail metadata."""

#         schema_class = "LDProofVCDetailSchema"

#     def __init__(
#         self,
#         credential: Optional[Union[dict, VerifiableCredential]],
#         options: Optional[Union[dict, LDProofVCOptions]],
#     ) -> None:
#         """Initialize the LDProofVCDetail instance."""
#         self.credential = credential
#         self.options = options

#     def __eq__(self, other: object) -> bool:
#         """Comparison between linked data vc details."""
#         if isinstance(other, LDProofVCDetail):
#             return self.credential == other.credential and self.options == other.options
#         return False

class VCDIDetail(BaseModel):
    """W3C verifiable credential detail"""
    class Meta:
        """VCDIDetail meatdata"""

        schema_class = "VCDIDetailSchema"

    def __init__(
        self,
        credential: Optional[Union[dict, VerifiableCredential]],
        options: Optional[Union[dict, VCDIDetailOptions]],
    ) -> None:
        self.credential = credential

    def __eq__(self, other: object) -> bool:
        """Comparison between W3C vc details."""
        if isinstance(other, VCDIDetail):
            return self.credential == other.credential and self.options == other.options
        return False

class VCDIDetailSchema(BaseModelSchema):
    """VC_DI verifiable credential detail schema."""

    class Meta:
        """Accept parameter overload."""

        unknown = INCLUDE
        model_class = VCDIDetail

    credential = fields.Nested(
        CredentialSchema(),
        required=True,
        metadata={
            "description": "Detail of the VC_DI Credential to be issued",
            "example": {
                "@id": "284d3996-ba85-45d9-964b-9fd5805517b6",
                "@type": "https://didcomm.org/issue-credential/2.0/issue-credential",
                "comment": "<some comment>",
                "formats": [
                    {
                        "attach_id": "5b38af88-d36f-4f77-bb7a-2f04ab806eb8",
                        "format": "didcomm/w3c-di-vc@v0.1"
                    }
                ],
                "credentials~attach": [
                    {
                        "@id": "5b38af88-d36f-4f77-bb7a-2f04ab806eb8",
                        "mime-type": "application/ld+json",
                        "data": {
                            "base64": "ewogICAgICAgICAgIkBjb250ZXogWwogICAgICAg...(clipped)...RNVmR0SXFXZhWXgySkJBIgAgfQogICAgICAgIH0="
                        }
                    }
                ]
            }
        },
    )

    options = fields.Nested(
        VCDIDetailOptionsSchema(),
        required=True,
        metadata={
            "description": (
                "Options for specifying how the linked data proof is created."
            ),
            "example": {"proofType": "Ed25519Signature2018"},
        },
    )