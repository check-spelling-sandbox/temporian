# Copyright 2021 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base calendar operator."""

from abc import ABC, abstractmethod

from temporian.core.data import dtype
from temporian.core.data.event import Event
from temporian.core.data.feature import Feature
from temporian.core.operators.base import Operator
from temporian.proto import core_pb2 as pb


class BaseCalendarOperator(Operator, ABC):
    """
    Base calendar operator to implement common logic.
    """

    def __init__(self, sampling: Event):
        super().__init__()

        # input
        self.add_input("sampling", sampling)

        output_feature = Feature(
            name=self.output_feature_name,
            dtype=dtype.INT32,
            sampling=sampling.sampling(),
            creator=self,
        )

        # output
        self.add_output(
            "event",
            Event(
                features=[output_feature],
                sampling=sampling.sampling(),
                creator=self,
            ),
        )

        self.check()

    @classmethod
    def build_op_definition(cls) -> pb.OperatorDef:
        return pb.OperatorDef(
            key=cls.operator_def_key,
            inputs=[pb.OperatorDef.Input(key="sampling")],
            outputs=[pb.OperatorDef.Output(key="event")],
        )

    @classmethod
    @property
    @abstractmethod
    def operator_def_key(cls) -> str:
        """Get the key of the operator definition."""

    @classmethod
    @property
    @abstractmethod
    def output_feature_name(cls) -> str:
        """Get the name of the generated feature in the output event."""