from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional, Set, Union

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, RootModel, conint, constr


class Status(Enum):
    SUPPORTED = 'SUPPORTED'
    UPDATE_RECOMMENDED = 'UPDATE_RECOMMENDED'


class UpdatePolicy(Enum):
    NONE = 'NONE'
    OPTIONAL = 'OPTIONAL'


class AppCompatibility(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    status: Status
    minimumRecommendedBuild: Optional[conint(ge=1)] = None
    latestBuild: Optional[conint(ge=1)] = None
    updatePolicy: Optional[UpdatePolicy] = None
    storeUrl: Optional[AnyUrl] = None


class Style(Enum):
    card = 'card'
    compact_card = 'compact_card'
    list_item = 'list_item'


class Type(Enum):
    text = 'text'


class Style1(Enum):
    title = 'title'
    subtitle = 'subtitle'
    body = 'body'
    label = 'label'


class Type1(Enum):
    feature = 'feature'


class Type2(Enum):
    spacer = 'spacer'


class Size(Enum):
    small = 'small'
    medium = 'medium'
    large = 'large'


class ResourceId(RootModel[constr(pattern=r'^[a-z][a-z0-9_]{1,63}$')]):
    root: constr(pattern=r'^[a-z][a-z0-9_]{1,63}$') = Field(
        ..., description='Stable public identifier.'
    )


class FieldError(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    field: str
    message: str


class XAppPlatform(Enum):
    android = 'android'


class XAppDistribution(Enum):
    full = 'full'
    qr = 'qr'
    nfc = 'nfc'
    payment = 'payment'
    internal = 'internal'
    beta = 'beta'
    production = 'production'


class XCountryCode(Enum):
    BR = 'BR'


class XCurrencyCode(Enum):
    BRL = 'BRL'


class FeaturePresentation(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    title: constr(min_length=1, max_length=100)
    subtitle: Optional[constr(max_length=200)] = None
    icon: ResourceId = Field(
        ..., description='Native asset key mapped by the mobile client.'
    )
    style: Style = Field(
        ..., description='Native visual variant, not arbitrary rendering code.'
    )


class ComponentBase(BaseModel):
    id: ResourceId
    type: str
    compatibilityVersion: Set[
        constr(pattern=r'^\d+(?:\.\d+)*$')
    ] = Field(
        ...,
        min_length=1,
        description=(
            'Renderer versions that can safely interpret this component '
            'representation.'
        ),
    )


class TextComponent(ComponentBase):
    id: ResourceId
    type: Literal['text']
    text: constr(min_length=1, max_length=500)
    style: Style1


class FeatureComponent(ComponentBase):
    id: ResourceId
    type: Literal['feature']
    featureId: ResourceId = Field(
        ..., description='Feature catalog reference validated before publication.'
    )


class SpacerComponent(ComponentBase):
    id: ResourceId
    type: Literal['spacer']
    size: Size


class Problem(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: AnyUrl
    title: str
    status: conint(ge=400, le=599)
    detail: str
    instance: Optional[str] = None
    code: constr(pattern=r'^(SDUI|APP|CONTEXT)_[A-Z0-9_]+$')
    correlationId: str
    errors: Optional[List[FieldError]] = None


class AppUpdateProblem(Problem):
    minimumSupportedBuild: conint(ge=1)
    minimumSupportedVersion: Optional[str] = None
    storeUrl: Optional[AnyUrl] = None


class Feature(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: ResourceId
    visible: bool = Field(
        ..., description='When false, the client must not render this feature.'
    )
    enabled: bool = Field(
        ..., description='Whether the rendered feature accepts interaction.'
    )
    disabledMessage: Optional[constr(max_length=200)] = Field(
        None,
        description='Safe localized explanation used only when the feature is disabled.',
    )
    presentation: FeaturePresentation


class ScreenComponent(
    RootModel[Union[TextComponent, FeatureComponent, SpacerComponent]]
):
    root: Union[TextComponent, FeatureComponent, SpacerComponent] = Field(
        ..., discriminator='type'
    )


class AppConfiguration(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    contractVersion: conint(ge=1) = Field(
        ..., description='Version of this configuration schema.'
    )
    revision: Optional[conint(ge=1)] = Field(
        None,
        description='Immutable content revision; independent from contractVersion.',
    )
    compatibility: Optional[AppCompatibility] = None
    features: List[Feature] = Field(
        ...,
        description='Evaluated feature catalog; internal rollout rules are omitted.',
        max_length=100,
    )


class Screen(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    contractVersion: conint(ge=1) = Field(
        ..., description='Version of this screen schema.'
    )
    revision: Optional[conint(ge=1)] = Field(
        None,
        description='Immutable content revision; independent from contractVersion.',
    )
    id: ResourceId
    title: Optional[constr(max_length=100)] = None
    components: List[ScreenComponent] = Field(
        ...,
        description='Native components rendered in the returned order.',
        max_length=200,
    )
