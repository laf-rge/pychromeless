# This code has been heavily modified from the original version.
#
# Copyright (c) 2018 Bao Nguyen <b@nqbao.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================
# https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84

import datetime
from typing import Any, Dict, List, Optional, TypeVar, Union, overload

import boto3

T = TypeVar("T", str, List[str], "SSMParameterStore")


class SSMParameterStore:
    """
    Provide a dictionary-like interface to access AWS SSM Parameter Store.
    """

    def __init__(
        self,
        prefix: Optional[str] = None,
        ssm_client: Optional[Any] = None,
        ttl: Optional[int] = None,
    ):
        """
        Initialize the SSMParameterStore.

        Args:
            prefix (Optional[str]): The prefix for parameter names.
            ssm_client (Optional[Any]): The boto3 SSM client.
            ttl (Optional[int]): Time-to-live for cache in seconds.
        """
        self._prefix: str = (prefix or "").rstrip("/") + "/"
        self._client: Any = ssm_client or boto3.client("ssm")
        self._keys: Optional[Dict[str, Dict[str, Any]]] = None
        self._substores: Dict[str, SSMParameterStore] = {}
        self._ttl: Optional[int] = ttl

    def get(
        self, name: str, **kwargs: Any
    ) -> Union[str, List[str], "SSMParameterStore"]:
        """
        Get a parameter or a substore.

        Args:
            name (str): The name of the parameter.

        Returns:
            Union[str, List[str], SSMParameterStore]: The value of the parameter or a substore.
        """
        assert name, "Name cannot be empty"
        if self._keys is None:
            self.refresh()
            if self._keys is None:
                raise KeyError(f"Key '{name}' not found after refresh")

        abs_key = f"{self._prefix}{name}"
        if name not in self._keys:
            if "default" in kwargs:
                return kwargs["default"]

            raise KeyError(name)
        elif self._keys[name]["type"] == "prefix":
            if abs_key not in self._substores:
                store = self.__class__(
                    prefix=abs_key, ssm_client=self._client, ttl=self._ttl
                )
                store._keys = self._keys[name]["children"]
                self._substores[abs_key] = store

            return self._substores[abs_key]
        else:
            value = self._get_value(name, abs_key)
            if value is None:
                raise KeyError(name)
            return value

    def refresh(self) -> None:
        """
        Refresh the parameter store by fetching parameters from SSM.
        """
        self._keys = {}
        self._substores = {}

        paginator = self._client.get_paginator("describe_parameters")
        pager = paginator.paginate(
            ParameterFilters=[
                {"Key": "Path", "Option": "Recursive", "Values": [self._prefix]}
            ]
        )

        for page in pager:
            for p in page["Parameters"]:
                paths = p["Name"][len(self._prefix) :].split("/")
                self._update_keys(self._keys, paths)

    @classmethod
    def _update_keys(cls, keys: Dict[str, Dict[str, Any]], paths: List[str]) -> None:
        """
        Update the keys dictionary with paths.

        Args:
            keys (Dict[str, Dict[str, Any]]): The keys dictionary.
            paths (List[str]): The list of path segments.
        """
        name = paths[0]

        # this is a prefix
        if len(paths) > 1:
            if name not in keys:
                keys[name] = {"type": "prefix", "children": {}}

            cls._update_keys(keys[name]["children"], paths[1:])
        else:
            keys[name] = {"type": "parameter", "expire": None}

    def keys(self) -> List[str]:
        """
        Get all keys in the parameter store.

        Returns:
            List[str]: The list of keys.
        """
        if self._keys is None:
            self.refresh()
            if self._keys is None:
                raise KeyError("Keys are not available after refresh")
        return list(self._keys.keys())

    def _get_value(self, name: str, abs_key: str) -> Optional[Union[str, List[str]]]:
        """
        Get the value of a parameter.

        Args:
            name (str): The name of the parameter.
            abs_key (str): The absolute key of the parameter.

        Returns:
            Optional[Union[str, List[str]]]: The value of the parameter.
        """
        if self._keys is None:
            raise KeyError(f"Key '{name}' not found in keys")

        entry = self._keys[name]

        # simple ttl
        if self._ttl is False or (
            entry["expire"] and entry["expire"] <= datetime.datetime.now()
        ):
            entry.pop("value", None)

        if "value" not in entry:
            parameter = self._client.get_parameter(Name=abs_key, WithDecryption=True)[
                "Parameter"
            ]
            value = parameter["Value"]
            if parameter["Type"] == "StringList":
                value = value.split(",")

            entry["value"] = value

            if self._ttl:
                entry["expire"] = datetime.datetime.now() + datetime.timedelta(
                    seconds=self._ttl
                )
            else:
                entry["expire"] = None

        return entry["value"]

    def __contains__(self, name: str) -> bool:
        """
        Check if a parameter exists in the store.

        Args:
            name (str): The name of the parameter.

        Returns:
            bool: True if the parameter exists, False otherwise.
        """
        try:
            self.get(name)
            return True
        except KeyError:
            return False

    @overload
    def __getitem__(self, name: str) -> Union[str, List[str], "SSMParameterStore"]: ...

    @overload
    def __getitem__(
        self, name: slice
    ) -> Dict[str, Union[str, List[str], "SSMParameterStore"]]: ...

    def __getitem__(self, name: Union[str, slice]) -> Union[
        str,
        List[str],
        "SSMParameterStore",
        Dict[str, Union[str, List[str], "SSMParameterStore"]],
    ]:
        """
        Get a parameter using the subscript notation.

        Args:
            name (Union[str, slice]): The name of the parameter or slice.

        Returns:
            Union[str, List[str], SSMParameterStore, Dict[str, Union[str, List[str], SSMParameterStore]]]:
                The value of the parameter, a substore, or a dict of values.
        """
        if isinstance(name, slice):
            # Handle slice notation (not implemented)
            raise NotImplementedError("Slice notation not supported")
        return self.get(name)

    def __class_getitem__(cls, item: Any) -> Any:
        """Support for generic type hints."""
        return cls

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set a parameter value. Not implemented.

        Args:
            key (str): The name of the parameter.
            value (Any): The value of the parameter.
        """
        raise NotImplementedError("Setting items is not supported")

    def __delitem__(self, name: str) -> None:
        """
        Delete a parameter. Not implemented.

        Args:
            name (str): The name of the parameter.
        """
        raise NotImplementedError("Deleting items is not supported")

    def __repr__(self) -> str:
        """
        Get the string representation of the parameter store.

        Returns:
            str: The string representation.
        """
        return f"ParameterStore[{self._prefix}]"
