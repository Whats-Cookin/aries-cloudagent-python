"""Credential artifacts."""

from typing import List, Mapping, Optional, Union

from marshmallow import EXCLUDE, ValidationError, fields, post_dump

from aries_cloudagent.vc.ld_proofs.constants import (
    CREDENTIALS_CONTEXT_V1_URL,
    VERIFIABLE_CREDENTIAL_TYPE,
)
from aries_cloudagent.vc.vc_ld.models.linked_data_proof import LinkedDataProofSchema

from ...messaging.models.base import BaseModel, BaseModelSchema
from ...messaging.valid import (
    CREDENTIAL_CONTEXT_EXAMPLE,
    CREDENTIAL_CONTEXT_VALIDATE,
    CREDENTIAL_SUBJECT_EXAMPLE,
    CREDENTIAL_SUBJECT_VALIDATE,
    CREDENTIAL_TYPE_EXAMPLE,
    CREDENTIAL_TYPE_VALIDATE,
    INDY_CRED_DEF_ID_EXAMPLE,
    INDY_CRED_DEF_ID_VALIDATE,
    INDY_REV_REG_ID_EXAMPLE,
    INDY_REV_REG_ID_VALIDATE,
    INDY_SCHEMA_ID_EXAMPLE,
    INDY_SCHEMA_ID_VALIDATE,
    NUM_STR_ANY_EXAMPLE,
    NUM_STR_ANY_VALIDATE,
    RFC3339_DATETIME_EXAMPLE,
    RFC3339_DATETIME_VALIDATE,
    DIDKey,
    DictOrDictListField,
    StrOrDictField,
    UriOrDictField,
)


class IndyAttrValue(BaseModel):
    """Indy attribute value."""

    class Meta:
        """Indy attribute value."""

        schema_class = "IndyAttrValueSchema"

    def __init__(self, raw: str = None, encoded: str = None, **kwargs):
        """Initialize indy (credential) attribute value."""
        super().__init__(**kwargs)
        self.raw = raw
        self.encoded = encoded


class IndyAttrValueSchema(BaseModelSchema):
    """Indy attribute value schema."""

    class Meta:
        """Indy attribute value schema metadata."""

        model_class = IndyAttrValue
        unknown = EXCLUDE

    raw = fields.Str(required=True, metadata={"description": "Attribute raw value"})
    encoded = fields.Str(
        required=True,
        validate=NUM_STR_ANY_VALIDATE,
        metadata={
            "description": "Attribute encoded value",
            "example": NUM_STR_ANY_EXAMPLE,
        },
    )


class DictWithIndyAttrValueSchema(fields.Dict):
    """Dict with indy attribute value schema."""

    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize dict with indy attribute value."""
        if not isinstance(value, dict):
            raise ValidationError("Value must be a dict.")

        errors = {}
        indy_attr_value_schema = IndyAttrValueSchema()

        for k, v in value.items():
            if isinstance(v, dict):
                validation_errors = indy_attr_value_schema.validate(v)
                if validation_errors:
                    errors[k] = validation_errors

        if errors:
            raise ValidationError(errors)

        return value


class IndyCredential(BaseModel):
    """Indy credential."""

    class Meta:
        """Indy credential metadata."""

        schema_class = "IndyCredentialSchema"

    def __init__(
        self,
        schema_id: str = None,
        cred_def_id: str = None,
        rev_reg_id: str = None,
        values: Mapping[str, IndyAttrValue] = None,
        signature: Mapping = None,
        signature_correctness_proof: Mapping = None,
        rev_reg: Mapping = None,
        witness: Mapping = None,
    ):
        """Initialize indy credential."""
        self.schema_id = schema_id
        self.cred_def_id = cred_def_id
        self.rev_reg_id = rev_reg_id
        self.values = values
        self.signature = signature
        self.signature_correctness_proof = signature_correctness_proof
        self.rev_reg = rev_reg
        self.witness = witness


class IndyCredentialSchema(BaseModelSchema):
    """Indy credential schema."""

    class Meta:
        """Indy credential schemametadata."""

        model_class = IndyCredential
        unknown = EXCLUDE

    schema_id = fields.Str(
        required=True,
        validate=INDY_SCHEMA_ID_VALIDATE,
        metadata={
            "description": "Schema identifier",
            "example": INDY_SCHEMA_ID_EXAMPLE,
        },
    )
    cred_def_id = fields.Str(
        required=True,
        validate=INDY_CRED_DEF_ID_VALIDATE,
        metadata={
            "description": "Credential definition identifier",
            "example": INDY_CRED_DEF_ID_EXAMPLE,
        },
    )
    rev_reg_id = fields.Str(
        allow_none=True,
        validate=INDY_REV_REG_ID_VALIDATE,
        metadata={
            "description": "Revocation registry identifier",
            "example": INDY_REV_REG_ID_EXAMPLE,
        },
    )
    values = DictWithIndyAttrValueSchema(
        required=True,
        metadata={"description": "Credential attributes"},
    )
    signature = fields.Dict(
        required=True, metadata={"description": "Credential signature"}
    )
    signature_correctness_proof = fields.Dict(
        required=True,
        metadata={"description": "Credential signature correctness proof"},
    )
    rev_reg = fields.Dict(
        allow_none=True, metadata={"description": "Revocation registry state"}
    )
    witness = fields.Dict(
        allow_none=True, metadata={"description": "Witness for revocation proof"}
    )


class VCDICredential(BaseModel):
    """VCDI credential."""

    class Meta:
        """VCDI credential metadata."""

        schema_class = "VCDICredentialSchema"

    def __init__(
        self,
        context: Optional[List[Union[str, dict]]] = None,
        type: Optional[List[str]] = None,
        issuer: Optional[Union[dict, str]] = None,
        credential_subject: Optional[Union[dict, List[dict]]] = None,
        proof: Optional[List[Union[dict, any]]] = None,
        issuance_date: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize the VerifiableCredential instance."""
        self._context = context or [CREDENTIALS_CONTEXT_V1_URL]
        self._type = type or [VERIFIABLE_CREDENTIAL_TYPE]
        self._issuer = issuer
        self._credential_subject = credential_subject
        self._proof = proof

        # TODO: proper date parsing
        self._issuance_date = issuance_date

        self.extra = kwargs


class VCDICredentialSchema(BaseModelSchema):
    """VCDI credential schema."""

    class Meta:
        """VCDI credential schemametadata."""

        model_class = VCDICredential
        unknown = EXCLUDE

    context = fields.List(
        UriOrDictField(required=True),
        data_key="@context",
        required=True,
        validate=CREDENTIAL_CONTEXT_VALIDATE,
        metadata={
            "description": "The JSON-LD context of the credential",
            "example": CREDENTIAL_CONTEXT_EXAMPLE,
        },
    )

    type = fields.List(
        fields.Str(required=True),
        required=True,
        validate=CREDENTIAL_TYPE_VALIDATE,
        metadata={
            "description": "The VCDI type of the credential",
            "example": CREDENTIAL_TYPE_EXAMPLE,
        },
    )

    issuer = StrOrDictField(
        required=True,
        metadata={
            "description": (
                "The JSON-LD Verifiable Credential Issuer. Either string of object with"
                " id field."
            ),
            "example": DIDKey.EXAMPLE,
        },
    )

    credential_subject = DictOrDictListField(
        required=True,
        data_key="credentialSubject",
        validate=CREDENTIAL_SUBJECT_VALIDATE,
        metadata={"example": CREDENTIAL_SUBJECT_EXAMPLE},
    )

    proof = fields.List(
        fields.Dict(keys=fields.Str(), values=fields.Str()),
        required=True,
        metadata={"description": ""},
    )

    issuance_date = fields.Str(
        data_key="issuanceDate",
        required=True,
        validate=RFC3339_DATETIME_VALIDATE,
        metadata={
            "description": "The issuance date",
            "example": RFC3339_DATETIME_EXAMPLE,
        },
    )

    @post_dump(pass_original=True)
    def add_unknown_properties(self, data: dict, original, **kwargs):
        """Add back unknown properties before outputting."""

        data.update(original.extra)

        return data
