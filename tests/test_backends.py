"""Test suite focusing on validation backend features."""

__author__ = "Jens Finkhaeuser"
__copyright__ = "Copyright (c) 2018 Jens Finkhaeuser"
__license__ = "MIT"
__all__ = ()

import pytest

from prance import BaseParser
from prance import ValidationError
from prance.util import validation_backends

from . import none_of


def test_bad_backend():
    with pytest.raises(ValueError):
        BaseParser("tests/specs/petstore.yaml", backend="does_not_exist")


@pytest.mark.skipif(none_of("flex"), reason="Missing dependencies: flex")
def test_flex_issue_5_integer_keys():
    # Must succeed with default (flex) parser; note the parser does not stringify the response code
    parser = BaseParser("tests/specs/issue_5.yaml", backend="flex")
    assert 200 in parser.specification["paths"]["/test"]["post"]["responses"]


@pytest.mark.skipif(none_of("flex"), reason="Missing dependencies: flex")
def test_flex_validate_success():
    parser = BaseParser("tests/specs/petstore.yaml", backend="flex")


@pytest.mark.skipif(none_of("flex"), reason="Missing dependencies: flex")
def test_flex_validate_failure():
    with pytest.raises(ValidationError):
        parser = BaseParser("tests/specs/missing_reference.yaml", backend="flex")


@pytest.mark.skipif(
    none_of("swagger-spec-validator"),
    reason="Missing dependencies: swagger-spec-validator",
)
def test_swagger_spec_validator_issue_5_integer_keys():
    # Must fail in implicit strict mode.
    with pytest.raises(ValidationError):
        BaseParser("tests/specs/issue_5.yaml", backend="swagger-spec-validator")

    # Must fail in explicit strict mode.
    with pytest.raises(ValidationError):
        BaseParser(
            "tests/specs/issue_5.yaml", backend="swagger-spec-validator", strict=True
        )

    # Must succeed in non-strict/lenient mode
    parser = BaseParser(
        "tests/specs/issue_5.yaml", backend="swagger-spec-validator", strict=False
    )
    assert "200" in parser.specification["paths"]["/test"]["post"]["responses"]


@pytest.mark.skipif(
    none_of("swagger-spec-validator"),
    reason="Missing dependencies: swagger-spec-validator",
)
def test_swagger_spec_validator_validate_success():
    parser = BaseParser("tests/specs/petstore.yaml", backend="swagger-spec-validator")


@pytest.mark.skipif(
    none_of("swagger-spec-validator"),
    reason="Missing dependencies: swagger-spec-validator",
)
def test_swagger_spec_validator_validate_failure():
    with pytest.raises(ValidationError):
        parser = BaseParser(
            "tests/specs/missing_reference.yaml", backend="swagger-spec-validator"
        )


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_spec_validator_issue_5_integer_keys():
    # Must fail in implicit strict mode.
    with pytest.raises(ValidationError):
        BaseParser("tests/specs/issue_5.yaml", backend="openapi-spec-validator")

    # Must fail in explicit strict mode.
    with pytest.raises(ValidationError):
        BaseParser(
            "tests/specs/issue_5.yaml", backend="openapi-spec-validator", strict=True
        )

    # Must succeed in non-strict/lenient mode
    parser = BaseParser(
        "tests/specs/issue_5.yaml", backend="openapi-spec-validator", strict=False
    )
    assert "200" in parser.specification["paths"]["/test"]["post"]["responses"]


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_spec_validator_issue_36_error_reporting():
    with pytest.raises(ValidationError, match=r"Strict mode enabled"):
        BaseParser("tests/specs/issue_36.yaml", backend="openapi-spec-validator")


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_spec_validator_validate_success():
    parser = BaseParser("tests/specs/petstore.yaml", backend="openapi-spec-validator")


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_spec_validator_validate_failure():
    with pytest.raises(ValidationError):
        parser = BaseParser(
            "tests/specs/missing_reference.yaml", backend="openapi-spec-validator"
        )


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_spec_validator_issue_20_spec_version_handling():
    # The spec is OpenAPI 3, but broken. Need to set 'strict' to False to stringify keys
    with pytest.raises(ValidationError):
        parser = BaseParser(
            "tests/specs/issue_20.yaml", backend="openapi-spec-validator", strict=False
        )

    # Lazy parsing should let us validate what's happening
    parser = BaseParser(
        "tests/specs/issue_20.yaml",
        backend="openapi-spec-validator",
        strict=False,
        lazy=True,
    )
    assert not parser.valid
    assert parser.version_parsed == ()

    with pytest.raises(ValidationError):
        parser.parse()

    # After parsing, the specs are not valid, but the correct version is
    # detected.
    assert not parser.valid
    assert parser.version_parsed == (3, 0, 0)


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_spec_validator_accepts_openapi_31_features():
    parser = BaseParser(
        "tests/specs/openapi_3_1_features.yaml", backend="openapi-spec-validator"
    )
    assert parser.valid
    assert parser.version_parsed == (3, 1, 0)
    # 3.1-specific top-level / info constructs
    assert (
        parser.specification["jsonSchemaDialect"]
        == "https://spec.openapis.org/oas/3.1/dialect/base"
    )
    assert parser.specification["info"]["license"]["identifier"] == "MIT"
    assert "itemUpdated" in parser.specification["webhooks"]
    # JSON Schema 2020-12 style keywords / type arrays
    item = parser.specification["components"]["schemas"]["Item"]
    assert item["properties"]["name"]["type"] == ["string", "null"]
    assert item["properties"]["score"]["exclusiveMinimum"] == 0
    # $ref siblings and reusable path items
    assert "description" in parser.specification["components"]["schemas"][
        "ItemRefWithSiblings"
    ]
    assert "Health" in parser.specification["components"]["pathItems"]


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_31_features_rejected_as_openapi_30():
    from prance.util import fs

    raw = fs.read_file("tests/specs/openapi_3_1_features.yaml")
    raw = raw.replace('openapi: "3.1.0"', 'openapi: "3.0.3"', 1)
    with pytest.raises(ValidationError):
        BaseParser(spec_string=raw, backend="openapi-spec-validator")


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_spec_validator_accepts_openapi_32_features():
    parser = BaseParser(
        "tests/specs/openapi_3_2_features.yaml", backend="openapi-spec-validator"
    )
    assert parser.valid
    assert parser.version_parsed == (3, 2, 0)
    # 3.2-specific document / server / tag constructs
    assert parser.specification["$self"] == "https://example.com/openapi.yaml"
    assert parser.specification["servers"][0]["name"] == "Production"
    search_tag = next(t for t in parser.specification["tags"] if t["name"] == "search")
    assert search_tag["parent"] == "root"
    assert search_tag["kind"] == "nav"
    # query method, querystring param, sequential media type, example shapes
    operation = parser.specification["paths"]["/search"]["query"]
    assert operation["parameters"][0]["in"] == "querystring"
    media = operation["responses"]["200"]["content"]["application/jsonl"]
    assert media["itemSchema"]["required"] == ["id"]
    assert media["examples"]["one"]["dataValue"] == {"id": "1"}
    assert "serializedValue" in media["examples"]["one"]
    # oauth2 deviceAuthorization flow
    flow = parser.specification["components"]["securitySchemes"]["deviceAuth"]["flows"][
        "deviceAuthorization"
    ]
    assert "deviceAuthorizationUrl" in flow


@pytest.mark.skipif(
    none_of("openapi-spec-validator"),
    reason="Missing dependencies: openapi-spec-validator",
)
def test_openapi_32_features_rejected_as_openapi_31():
    from prance.util import fs

    raw = fs.read_file("tests/specs/openapi_3_2_features.yaml")
    raw = raw.replace('openapi: "3.2.0"', 'openapi: "3.1.0"', 1)
    with pytest.raises(ValidationError):
        BaseParser(spec_string=raw, backend="openapi-spec-validator")


@pytest.mark.skipif(
    none_of("flex"),
    reason="Missing dependencies: flex",
)
def test_flex_rejects_openapi_31():
    with pytest.raises(ValidationError, match="Version mismatch"):
        BaseParser("tests/specs/openapi_3_1_features.yaml", backend="flex")


@pytest.mark.skipif(
    none_of("swagger-spec-validator"),
    reason="Missing dependencies: swagger-spec-validator",
)
def test_swagger_spec_validator_rejects_openapi_31():
    with pytest.raises(ValidationError, match="Version mismatch"):
        BaseParser(
            "tests/specs/openapi_3_1_features.yaml", backend="swagger-spec-validator"
        )


def test_validation_backends_prefer_osv():
    backends = validation_backends()
    if "openapi-spec-validator" in backends:
        assert backends[0] == "openapi-spec-validator"
