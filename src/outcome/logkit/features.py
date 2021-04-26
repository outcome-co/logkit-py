"""Logkit optional features."""

from outcome.utils import feature_set

feature_set.register_feature('co.outcome.logkit.use_stackdriver', 'auto', feature_set.FeatureType.string)
