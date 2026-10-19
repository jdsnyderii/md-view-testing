from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.12.0"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'mdportal',
     'default_range': 'string',
     'description': 'Configuration for mdportal named mount roots. Matches app.py '
                    '(load_roots / LocalDir / GitHub / HTTP / S3).\n'
                    'Root kinds are modeled as subclasses of RootSpec with type as '
                    'a type designator (designates_type). Instance YAML uses type: '
                    'dir|github|http|s3 matching the subclass names.\n'
                    'String fields may contain ${ENV} or ${ENV:-default}; '
                    'expansion is runtime.\n',
     'id': 'https://example.org/mdportal/roots',
     'imports': ['linkml:types'],
     'name': 'mdportal_roots',
     'prefixes': {'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'mdportal': {'prefix_prefix': 'mdportal',
                               'prefix_reference': 'https://example.org/mdportal/'}},
     'source_file': 'roots.linkml.yaml',
     'title': 'mdportal roots.yaml'} )


class RootsConfig(ConfiguredBaseModel):
    """
    Top-level roots.yaml document
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/mdportal/roots', 'tree_root': True})

    home: str = Field(default=..., description="""Default document as \"<rootName>/<path>\" (e.g. portalRoot/index.md)""", json_schema_extra = { "linkml_meta": {'domain_of': ['RootsConfig']} })
    roots: dict[str, Annotated[Union[Dir, Github, Http, S3], Field(discriminator="type")]] = Field(default=..., description="""Map of root name to root specification""", json_schema_extra = { "linkml_meta": {'domain_of': ['RootsConfig']} })

    @field_validator('home')
    def pattern_home(cls, v):
        pattern=re.compile(r"^[^/]+/.+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.search(element):
                    err_msg = f"Invalid home format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.search(v):
            err_msg = f"Invalid home format: {v}"
            raise ValueError(err_msg)
        return v


class RootSpec(ConfiguredBaseModel):
    """
    Named mount root; concrete kind selected by type
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'abstract': True, 'from_schema': 'https://example.org/mdportal/roots'})

    name: str = Field(default=..., description="""Root name (YAML map key); becomes $name in includes""", json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })
    type: Literal["RootSpec"] = Field(default="RootSpec", description="""Kind of root — designator for the concrete subclass""", json_schema_extra = { "linkml_meta": {'designates_type': True, 'domain_of': ['RootSpec']} })
    ttl: Optional[int] = Field(default=None, description="""Cache TTL seconds for remote roots (default 60)""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })


class Dir(RootSpec):
    """
    Local directory (bind-mount in Docker)
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/mdportal/roots'})

    path: str = Field(default=..., description="""Filesystem path (absolute in containers)""", json_schema_extra = { "linkml_meta": {'domain_of': ['dir']} })
    name: str = Field(default=..., description="""Root name (YAML map key); becomes $name in includes""", json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })
    type: Literal["dir"] = Field(default="dir", description="""Kind of root — designator for the concrete subclass""", json_schema_extra = { "linkml_meta": {'designates_type': True, 'domain_of': ['RootSpec']} })
    ttl: Optional[int] = Field(default=None, description="""Cache TTL seconds for remote roots (default 60)""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })


class Github(RootSpec):
    """
    GitHub repo via raw.githubusercontent.com
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/mdportal/roots'})

    repo: str = Field(default=..., description="""owner/name""", json_schema_extra = { "linkml_meta": {'domain_of': ['github']} })
    ref: Optional[str] = Field(default=None, description="""Branch, tag, or commit (default main)""", json_schema_extra = { "linkml_meta": {'domain_of': ['github']} })
    subdir: Optional[str] = Field(default=None, description="""Optional path within the repo""", json_schema_extra = { "linkml_meta": {'domain_of': ['github']} })
    token: Optional[str] = Field(default=None, description="""GitHub token; empty means public""", json_schema_extra = { "linkml_meta": {'domain_of': ['github']} })
    name: str = Field(default=..., description="""Root name (YAML map key); becomes $name in includes""", json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })
    type: Literal["github"] = Field(default="github", description="""Kind of root — designator for the concrete subclass""", json_schema_extra = { "linkml_meta": {'designates_type': True, 'domain_of': ['RootSpec']} })
    ttl: Optional[int] = Field(default=None, description="""Cache TTL seconds for remote roots (default 60)""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })

    @field_validator('repo')
    def pattern_repo(cls, v):
        pattern=re.compile(r"^[^/]+/[^/]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.search(element):
                    err_msg = f"Invalid repo format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.search(v):
            err_msg = f"Invalid repo format: {v}"
            raise ValueError(err_msg)
        return v


class Http(RootSpec):
    """
    Arbitrary http(s) base URL
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/mdportal/roots'})

    url: str = Field(default=..., description="""Base http(s) URL; docs only supply the path under it""", json_schema_extra = { "linkml_meta": {'domain_of': ['http']} })
    headers: Optional[list[str]] = Field(default=None, description="""Extra request headers (values may use ${ENV})""", json_schema_extra = { "linkml_meta": {'domain_of': ['http']} })
    timeout: Optional[int] = Field(default=None, description="""Timeout seconds (default 10)""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['http']} })
    name: str = Field(default=..., description="""Root name (YAML map key); becomes $name in includes""", json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })
    type: Literal["http"] = Field(default="http", description="""Kind of root — designator for the concrete subclass""", json_schema_extra = { "linkml_meta": {'designates_type': True, 'domain_of': ['RootSpec']} })
    ttl: Optional[int] = Field(default=None, description="""Cache TTL seconds for remote roots (default 60)""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })

    @field_validator('url')
    def pattern_url(cls, v):
        pattern=re.compile(r"^https?://")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.search(element):
                    err_msg = f"Invalid url format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.search(v):
            err_msg = f"Invalid url format: {v}"
            raise ValueError(err_msg)
        return v


class S3(RootSpec):
    """
    S3 or S3-compatible bucket
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/mdportal/roots'})

    bucket: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['s3']} })
    prefix: Optional[str] = Field(default=None, description="""Key prefix; object key is prefix/rel""", json_schema_extra = { "linkml_meta": {'domain_of': ['s3']} })
    region: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['s3']} })
    endpoint_url: Optional[str] = Field(default=None, description="""S3-compatible endpoint (MinIO, R2, …)""", json_schema_extra = { "linkml_meta": {'domain_of': ['s3']} })
    profile: Optional[str] = Field(default=None, description="""boto3 profile name""", json_schema_extra = { "linkml_meta": {'domain_of': ['s3']} })
    name: str = Field(default=..., description="""Root name (YAML map key); becomes $name in includes""", json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })
    type: Literal["s3"] = Field(default="s3", description="""Kind of root — designator for the concrete subclass""", json_schema_extra = { "linkml_meta": {'designates_type': True, 'domain_of': ['RootSpec']} })
    ttl: Optional[int] = Field(default=None, description="""Cache TTL seconds for remote roots (default 60)""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['RootSpec']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
RootsConfig.model_rebuild()
RootSpec.model_rebuild()
Dir.model_rebuild()
Github.model_rebuild()
Http.model_rebuild()
S3.model_rebuild()
