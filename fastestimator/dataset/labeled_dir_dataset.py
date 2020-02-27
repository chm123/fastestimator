# Copyright 2019 The FastEstimator Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import os
from collections import deque
from typing import Optional, Dict, Sequence, Iterable, Any, List

from fastestimator.dataset.dataset import FEDataset


class LabeledDirDataset(FEDataset):
    """ A dataset which reads files from a folder hierarchy like root/class(/es)/data.file

    Args:
        root_dir: The path to the directory containing data sorted by folders
        data_key: What key to assign to the data values in the data dictionary
        label_key: What key to assign to the label values in the data dictionary
        label_mapping: A dictionary defining the mapping to use. If not provided will map classes to int labels
        file_extension: If provided then only files ending with the file_extension will be included
    """
    data: Dict[int, Dict[str, Any]]

    def __init__(self,
                 root_dir: str,
                 data_key: str = "x",
                 label_key: str = "y",
                 label_mapping: Optional[Dict[str, Any]] = None,
                 file_extension: Optional[str] = None):
        # Recursively find all the data
        root_dir = os.path.normpath(root_dir)
        data = {}
        keys = deque([""])
        for _, dirs, entries in os.walk(root_dir):
            key = keys.popleft()
            dirs = [os.path.join(key, d) for d in dirs]
            dirs.reverse()
            keys.extendleft(dirs)
            entries = [
                os.path.join(key, e) for e in entries if not e.startswith(".") and e.endswith(file_extension or "")
            ]
            if entries:
                data[key] = entries
        # Compute label mappings
        self.mapping = label_mapping or {label: idx for idx, label in enumerate(sorted(data.keys()))}
        assert self.mapping.keys() >= data.keys(), \
            "Mapping provided to LabeledDirDataset is missing key(s): {}".format(
                data.keys() - self.mapping.keys())
        # Store the data by index
        self.data = {}
        idx = 0
        for key, values in data.items():
            label = self.mapping[key]
            for value in values:
                self.data[idx] = {data_key: os.path.join(root_dir, value), label_key: label}
                idx += 1

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index: int):
        return self.data[index]

    def get_mapping(self) -> Dict[str, Any]:
        return self.mapping

    @classmethod
    def _skip_init(cls, data: Dict[int, Dict[str, Any]], mapping: Dict[str, Any], **kwargs) -> 'LabeledDirDataset':
        obj = cls.__new__(cls)
        obj.data = data
        obj.mapping = mapping
        for k, v in kwargs.items():
            obj.__setattr__(k, v)
        return obj

    def _do_split(self, splits: Sequence[Iterable[int]]) -> List['LabeledDirDataset']:
        results = []
        for split in splits:
            data = {new_idx: self.data.pop(old_idx) for new_idx, old_idx in enumerate(split)}
            results.append(LabeledDirDataset._skip_init(data, self.mapping))
        # Re-key the remaining data to be contiguous from 0 to new max index
        self.data = {new_idx: v for new_idx, (old_idx, v) in enumerate(self.data.items())}
        return results
