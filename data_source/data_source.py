#
# Copyright © 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#
import abc

class DataSourceInterface(abc.ABC):

    @abc.abstractmethod
    def initialize(self):
        # The function should initialize any connections that need
        # to be made or any variables that will be required
        pass

    @abc.abstractmethod
    def capture_data(self):
        # The function should capture a single data point from a source or device
        pass

    @abc.abstractmethod
    def clean_local_cache(self):
        # The function should clear the local disk if it is being used
        pass
    