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

from typing import Dict, Optional

import numpy as np

from temporian.core.operators.since_last import SinceLast
from temporian.implementation.numpy import implementation_lib
from temporian.implementation.numpy.data.event_set import DTYPE_REVERSE_MAPPING
from temporian.implementation.numpy.data.event_set import IndexData
from temporian.implementation.numpy.data.event_set import EventSet
from temporian.implementation.numpy.operators.base import OperatorImplementation
from temporian.implementation.numpy_cc.operators import operators_cc


class SinceLastNumpyImplementation(OperatorImplementation):
    """Numpy implementation of the since last operator."""

    def __init__(self, operator: SinceLast) -> None:
        super().__init__(operator)
        assert isinstance(operator, SinceLast)

    def __call__(
        self, input: EventSet, sampling: Optional[EventSet] = None
    ) -> Dict[str, EventSet]:
        assert isinstance(self.operator, SinceLast)
        assert self.operator.has_sampling == (sampling is not None)

        output_event = EventSet(
            {},
            feature_names=["since_last"],
            index_names=input.index_names,
            is_unix_timestamp=input.is_unix_timestamp,
        )

        for index_key, index_data in input.iterindex():
            if sampling is not None:
                sampling_timestamps = sampling.data[index_key].timestamps
                feature_values = operators_cc.since_last(
                    index_data.timestamps, sampling_timestamps
                )
                output_event[index_key] = IndexData(
                    [feature_values], sampling_timestamps
                )
            else:
                # TODO: Avoid memory copy.
                feature_values = np.concatenate(
                    [[np.nan], np.diff(index_data.timestamps)]
                )
                output_event[index_key] = IndexData(
                    [feature_values], index_data.timestamps
                )

        return {"output": output_event}


implementation_lib.register_operator_implementation(
    SinceLast, SinceLastNumpyImplementation
)
