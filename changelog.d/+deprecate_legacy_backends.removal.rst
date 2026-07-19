Deprecate the ``flex`` and ``swagger-spec-validator`` backends (and the
``[flex]`` / ``[ssv]`` extras). Selecting them emits ``DeprecationWarning``;
prefer ``openapi-spec-validator`` via ``prance[osv]``.
