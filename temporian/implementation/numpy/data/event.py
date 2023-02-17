from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd

from temporian.core.data.event import Event
from temporian.core.data.feature import Feature
from temporian.core.data import dtype
from temporian.implementation.numpy.data.sampling import NumpySampling

DTYPE_MAPPING = {
    np.float64: dtype.FLOAT64,
    np.float32: dtype.FLOAT32,
    np.int64: dtype.INT64,
    np.int32: dtype.INT32,
}


class NumpyFeature:
    def __init__(self, name: str, data: np.ndarray) -> None:
        if len(data.shape) > 1:
            raise ValueError(
                "NumpyFeatures can only be created from flat arrays. Passed"
                f" input's shape: {len(data.shape)}"
            )
        if data.dtype.type is not np.string_:
            if data.dtype.type not in DTYPE_MAPPING:
                raise ValueError(
                    f"Unsupported dtype {data.dtype} for NumpyFeature."
                    f" Supported dtypes: {DTYPE_MAPPING.keys()}"
                )

        self.name = name
        self.data = data
        self.dtype = data.dtype.type

    def __repr__(self) -> str:
        return f"{self.name}: {self.data.__repr__()}"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, NumpyFeature):
            return False

        if self.name != __o.name:
            return False

        if not np.array_equal(self.data, __o.data, equal_nan=True):
            return False

        return True

    def core_dtype(self) -> Any:
        if self.dtype.type is np.string_:
            return dtype.STRING
        return DTYPE_MAPPING[self.dtype]


class NumpyEvent:
    def __init__(
        self,
        data: Dict[Tuple, List[NumpyFeature]],
        sampling: NumpySampling,
    ) -> None:
        self.data = data
        self.sampling = sampling

    @property
    def feature_count(self) -> int:
        if len(self.data.keys()) == 0:
            return 0

        first_index = next(iter(self.data))
        return len(self.data[first_index])

    @property
    def feature_names(self) -> List[str]:
        if len(self.data.keys()) == 0:
            return []

        # Only look at the feature in the first index
        # to get the feature names. All features in all
        # indexes should have the same names
        first_index = next(iter(self.data))
        return [feature.name for feature in self.data[first_index]]

    def schema(self) -> Event:
        return Event(
            features=[
                feature.schema() for feature in list(self.data.values())[0]
            ],
            sampling=self.sampling.names,
        )

    @staticmethod
    def dataframe_to_event(
        df: pd.DataFrame,
        timestamp_index_name: str = "timestamp",
    ) -> "NumpyEvent":
        """Function to convert a pandas DataFrame to a NumpyEvent

        Args:
            df: DataFrame to convert to NumpyEvent
            timestamp_index_name: Name for timestamp index. Defaults to "timestamp".

        Returns:
            NumpyEvent: NumpyEvent created from DataFrame
        """

        # create df without timestamp in index in order to group each index
        # with its timestamps for conversion
        df_without_ts_idx = df.reset_index(level="timestamp")
        index_without_ts = df_without_ts_idx.index
        sampling = {}
        data = {}

        for index in index_without_ts.unique():
            # get the df grouped by timestamp in a specific index
            index_group = df.groupby(index_without_ts.names).get_group(index)

            # get timestamps of group
            timestamps = index_group.index.get_level_values(
                timestamp_index_name
            )
            timestamps = timestamps.to_numpy()

            # convert to tuple if not already, useful for single index
            if type(index) != tuple:
                index = (index,)

            sampling[index] = timestamps

            # create NumpyFeatures for each column in index_group
            columns = index_group.loc[index]
            data[index] = []
            for column_name in index_group.columns:
                data[index].append(
                    NumpyFeature(column_name, columns[column_name].to_numpy())
                )

        numpy_sampling = NumpySampling(
            names=index_without_ts.names, data=sampling
        )

        return NumpyEvent(data=data, sampling=numpy_sampling)

    @staticmethod
    def event_to_dataframe(event: "NumpyEvent") -> pd.DataFrame:
        """Function to convert a NumpyEvent to a pandas DataFrame

        Args:
            event: NumpyEvent to convert to DataFrame

        Returns:
            pd.DataFrame: DataFrame created from NumpyEvent
        """
        df_index = event.sampling.names + ["timestamp"]
        df_features = event.feature_names
        columns = df_index + df_features

        df = pd.DataFrame(data=[], columns=columns).set_index(df_index)

        for index, features in event.data.items():
            timestamps_index = event.sampling.data[index]
            for i, timestamp in enumerate(timestamps_index):
                # add timestamp to index
                new_index = index + (timestamp,)
                df.loc[new_index, df_features] = [
                    feature.data[i] for feature in features
                ]

        # Convert to original dtypes, can be more efficient
        first_index = list(event.data.keys())[0]
        first_features = event.data[first_index]
        df = df.astype(
            {feature.name: type(feature.data[0]) for feature in first_features}
        )

        return df

    def __repr__(self) -> str:
        return self.data.__repr__() + " " + self.sampling.__repr__()

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, NumpyEvent):
            return False

        # Check equal sampling and index values
        if self.sampling != __o.sampling:
            return False

        # Check same features
        if self.feature_names != __o.feature_names:
            return False

        # Check each feature is equal in each index
        for index in self.data.keys():
            # Check both feature list are equal
            if self.data[index] != __o.data[index]:
                return False

        return True
