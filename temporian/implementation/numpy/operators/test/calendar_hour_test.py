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

from absl.testing import absltest
import numpy as np
import pandas as pd

from temporian.core.operators.calendar.hour import (
    CalendarHourOperator,
)
from temporian.implementation.numpy.data.event import NumpyEvent
from temporian.implementation.numpy.data.event import NumpyFeature
from temporian.implementation.numpy.operators.calendar.hour import (
    CalendarHourNumpyImplementation,
)
from temporian.core.data import dtype


class CalendarHourNumpyImplementationTest(absltest.TestCase):
    """Test numpy implementation of calendar_hour operator."""

    def test_basic(self) -> None:
        "Basic test with flat event."
        input_event_data = NumpyEvent.from_dataframe(
            pd.DataFrame(
                data=[
                    [pd.to_datetime("1970-01-01 00:00:00", utc=True)],
                    [pd.to_datetime("1970-01-01 01:00:00", utc=True)],
                    [pd.to_datetime("1970-01-01 01:59:59", utc=True)],
                    [pd.to_datetime("2023-06-06 12:00:00", utc=True)],
                    [pd.to_datetime("2023-06-06 23:59:59", utc=True)],
                ],
                columns=["timestamp"],
            ),
        )

        input_event = input_event_data.schema()

        output_event_data = NumpyEvent(
            data={
                (): [
                    NumpyFeature(
                        name="calendar_hour",
                        data=np.array([0, 1, 1, 12, 23]),
                    ),
                ],
            },
            sampling=input_event_data.sampling,
        )

        operator = CalendarHourOperator(input_event)
        impl = CalendarHourNumpyImplementation(operator)
        output = impl.call(sampling=input_event_data)

        self.assertTrue(output_event_data == output["event"])
        self.assertTrue(
            output["event"]._first_index_features[0].dtype == dtype.INT32
        )


if __name__ == "__main__":
    absltest.main()
