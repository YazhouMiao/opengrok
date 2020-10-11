#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# See LICENSE.txt included in this distribution for the specific
# language governing permissions and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at LICENSE.txt.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#

import abc

from ..utils.command import Command


class RepositoryException(Exception):
    """
    Exception returned when repository operation failed.
    """
    pass


class Repository:
    """
    abstract class wrapper for Source Code Management repository
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, logger, path, project, configured_commands, env, hooks,
                 timeout):
        self.logger = logger
        self.path = path
        self.project = project
        self.timeout = timeout
        self.configured_commands = configured_commands
        if env:
            self.env = env
        else:
            self.env = {}

    def __str__(self):
        return self.path

    def getCommand(self, cmd, **kwargs):
        kwargs['timeout'] = self.timeout
        return Command(cmd, **kwargs)

    def sync(self):
        # Eventually, there might be per-repository hooks added here.
        if isinstance(self.configured_commands, dict) and self.configured_commands.get('sync'):
            return self._run_command(self.listify(self.configured_commands['sync']))
        return self.reposync()

    @abc.abstractmethod
    def reposync(self):
        """
        Synchronize the repository by running sync command specific for
        given repository type.

        Return 1 on failure, 0 on success.
        """
        raise NotImplementedError()

    def incoming(self):
        """
        Check if there are any incoming changes.

        Return True if so, False otherwise.
        """
        if isinstance(self.configured_commands, dict) and self.configured_commands.get('incoming'):
            return self._run_command(self.listify(self.configured_commands['incoming'])) != 0
        return self.incoming_check()

    def incoming_check(self):
        """
        Check if there are any incoming changes.

        Return True if so, False otherwise.
        """
        return True

    def _run_command(self, command):
        """
        Execute the command.

        :param command: the command
        :return: 0 on success execution, 1 otherwise
        """
        cmd = self.getCommand(command, work_dir=self.path, env_vars=self.env, logger=self.logger)
        cmd.execute()
        if cmd.getretcode() != 0 or cmd.getstate() != Command.FINISHED:
            self.logger.debug("output of '{}':".format(cmd))
            if cmd.getoutputstr():
                self.logger.debug(cmd.getoutputstr())
            if cmd.geterroutputstr():
                self.logger.debug(cmd.geterroutputstr())
            cmd.log_error("failed to perform command")
            return 1
        if cmd.getoutputstr():
            self.logger.debug("output of '{}':".format(cmd))
            self.logger.debug(cmd.getoutputstr())
        return 0

    @staticmethod
    def _repository_command(configured_commands, default=lambda: None):
        """
        Get the repository command, or use default supplier.

        :param configured_commands: commands section from configuration for this repository type
        :param default: the supplier of default command
        :return: the repository command
        """
        if isinstance(configured_commands, str):
            return configured_commands
        elif isinstance(configured_commands, dict) and configured_commands.get('command'):
            return configured_commands['command']

        return default()

    @staticmethod
    def listify(object):
        return object if isinstance(object, list) or isinstance(object, tuple) else [object]
