from enum import EnumMeta
from typing import Dict


class BaseFlagMeta(EnumMeta):
    # Override EnumMeta.__call__ to allow use of ``Flag(Some_Flag=True)``
    # Alternative for using bitwise operators

    def __call__(cls, value: int = 0, *args, **kwargs: Dict[str, bool]):
        """If you dont like using bitwise operators, 
        or would like a simple way of creating flags.

        Look no further!

        .. rubric:: Usage

        .. code-block:: py

            # Example Using ``acord.Permissions``
            from acord import Role, Permissions

            permissions = Role.permissions

            from_int = Permissions(permissions)
            my_permissions = Permissions(CONNECT=True, STREAM=True, SPEAK=True)

        Parameters
        ----------
        value: :class:`int`
            Value of flag
        **kwargs: Dict[:class:`str`, :class:`bool`]
            Name of flags you want to use,
            value must be set to ``True``!
        """
        # get the value of an Enum
        value = getattr(value, 'value', value)

        enum = super(cls.__class__, cls).__call__(int(value))

        for flag_name, flag_value in kwargs.items():
            if flag_value is True:
                enum |= getattr(cls, flag_name)
        
        return enum
