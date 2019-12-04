#
# Copyright © 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#
import abc

class ObjectStoreInterface(abc.ABC):

    @abc.abstractmethod
    def initialize(self):
        # The function should initialize any connections that need
        # to be made or any variables that will be required
        pass

    @abc.abstractmethod
    def upload(self):
        # The function should upload an object to the object store
        pass

    @abc.abstractmethod
    def download(self):
        # The function should download and object from the object store
        pass

    @abc.abstractmethod
    def delete(self):
        # The function should delete an object from the object store
        pass

    @abc.abstractmethod
    def list_objects(self):
        # The function should list the objects from an object store
        pass
    