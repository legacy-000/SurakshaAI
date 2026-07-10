class FeatureFlags:
    def __init__(self):
        self._flags = {
            "voice_enabled": True,
            "kannada_enabled": True,
            "forecast_enabled": True,
            "network_analysis_enabled": True,
            "sociological_enabled": True,
            "financial_extension_enabled": True,
        }

    def is_enabled(self, flag_name: str) -> bool:
        return self._flags.get(flag_name, False)

    def set_flag(self, flag_name: str, value: bool):
        self._flags[flag_name] = value

    def all_flags(self):
        return dict(self._flags)


feature_flags = FeatureFlags()
