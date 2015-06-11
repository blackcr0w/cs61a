PK     8jDF��   �      __main__.pyimport sys

if sys.version_info[0] < 3:
	sys.exit("ok requires Python 3. \nFor more info: http://www-inst.eecs.berkeley.edu/~cs61a/fa14/lab/lab01/#installing-python")

from client.cli import ok

if __name__ == '__main__':
    ok.main()

PK     \kDF�'��   �      client/__init__.py__version__ = 'v1.3.13'

import os
import sys

sys.path.insert(0, '')
# Add directory in which the ok.zip is stored to sys.path.
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
PK     \kDF0ZW$  $     client/exceptions.py"""Client exceptions."""

class OkException(BaseException):
    """Base exception class for OK."""

class ProtocolException(OkException):
    """Exceptions related to protocol errors."""

# TODO(albert): extend from a base class designed for student bugs.
class Timeout(OkException):
    """Exception for timeouts."""
    _message = 'Evaluation timed out!'

    def __init__(self, timeout):
        """Constructor.

        PARAMTERS:
        timeout -- int; number of seconds before timeout error occurred
        """
        super().__init__(self)
        self.timeout = timeout
        self.message = self._message

class LoadingException(OkException):
    """Exception related to loading assignments."""

class SerializeException(LoadingException):
    """Exceptions related to de/serialization."""

PK     8jDF               client/sources/__init__.pyPK     8jDF            !   client/sources/common/__init__.pyPK     8jDFi�\��  �     client/sources/common/models.py"""Models for serialization of tests."""

from client.sources.common import core

class Test(core.Serializable):
    name = core.String()
    points = core.Float()
    partner = core.Int(optional=True)

    def run(self):
        """Subclasses should override this method to run tests."""
        raise NotImplementedError

    def score(self):
        """Subclasses should override this method to score the test."""
        raise NotImplementedError

    def unlock(self, interact):
        """Subclasses should override this method to lock the test."""
        raise NotImplementedError

    def lock(self, hash_fn):
        """Subclasses should override this method to lock the test."""
        raise NotImplementedError

    def dump(self):
        """Subclasses should override this method for serialization."""
        raise NotImplementedError

class Case(core.Serializable):
    """Abstract case class."""

    hidden = core.Boolean(default=False)
    locked = core.Boolean(optional=True)

    def run(self):
        """Subclasses should override this method for running a test case.

        RETURNS:
        bool; True if the test case passes, False otherwise.
        """
        raise NotImplementedError

    def lock(self, hash_fn):
        """Subclasses should override this method for locking a test case.

        This method should mutate the object into a locked state.

        PARAMETERS:
        hash_fn -- function; computes the hash code of a given string.
        """
        raise NotImplementedError

    def unlock(self, interact):
        """Subclasses should override this method for unlocking a test case.

        It is the responsibility of the the subclass to make any changes to the
        test case, including setting its locked field to False.

        PARAMETERS:
        interact -- function; handles user interaction during the unlocking
                    phase.
        """
        raise NotImplementedError

PK     8jDF�-2��  �     client/sources/common/core.pyfrom client import exceptions as ex
import collections

###############
# Field types #
###############

class NoValue(object):
    pass

NoValue = NoValue()

class Field(object):
    _default = NoValue

    def __init__(self, optional=False, **kargs):
        self._optional = optional
        if 'default' in kargs:
            value = kargs['default']
            if not self.is_valid(value):
                raise ex.SerializeException('Invalid default: {}'.format(value))
            self._optional = True
            self._default = value

    @property
    def optional(self):
        return self._optional

    @property
    def default(self):
        return self._default

    def is_valid(self, value):
        """Subclasses should override this method for field validation."""
        return True

    def coerce(self, value):
        """Subclasses should override this method for type coercion.

        Default version will simply return the argument. If the argument
        is not valid, a SerializeException is raised.

        For primitives like booleans, ints, floats, and strings, use
        this default version to avoid unintended type conversions."""
        if not self.is_valid(value):
            raise ex.SerializeException('{} is not a valid value for '
                                        'type {}'.format(value, self.__class__.__name__))
        return value

    def to_json(self, value):
        """Subclasses should override this method for JSON encoding."""
        if not self.is_valid(value):
            raise ex.SerializeException('Invalid value: {}'.format(value))
        return value

class Boolean(Field):
    def is_valid(self, value):
        return value in (True, False)

class Int(Field):
    def is_valid(self, value):
        return type(value) == int

class Float(Field):
    def is_valid(self, value):
        return type(value) in (int, float)

class String(Field):
    def is_valid(self, value):
        return type(value) == str

class List(Field):
    def __init__(self, type=None, **kargs):
        """Constructor for a List field.

        PARAMETERS:
        type -- type; if type is None, the List can be heterogeneous.
                Otherwise, the List must be homogeneous with elements
                of the specified type.
        """
        super().__init__(**kargs)
        self._type = type

    def is_valid(self, value):
        valid = type(value) == list
        if self._type is not None:
            valid &= all(isinstance(e, self._type) for e in value)
        return valid

    def coerce(self, value):
        if self._type is None:
            try:
                return list(value)
            except TypeError as e:
                raise ex.SerializeException(str(e))
        else:
            # TODO(albert): find a way to do better element-wise type coercion
            # so that constructors can take additional arguments
            try:
                return [self._type(elem) for elem in value]
            except TypeError as e:
                raise ex.SerializeException(str(e))

    def to_json(self, value):
        value = super().to_json(value)
        return [elem.to_json() if hasattr(elem, 'to_json') else elem
                             for elem in value]

class Dict(Field):
    def __init__(self, keys=None, values=None, ordered=False, **kargs):
        super().__init__(**kargs)
        self._keys = keys
        self._values = values
        self._constructor = collections.OrderedDict if ordered else dict
        self._ordered = ordered

    @property
    def ordered(self):
        return self._ordered

    def is_valid(self, value):
        valid = isinstance(value, dict)
        if self._keys is not None:
            valid &= all(isinstance(k, self._keys) for k in value)
        if self._values is not None:
            valid &= all(isinstance(v, self._values) for v in value.values())
        return valid

    def coerce(self, value):
        try:
            coerced = self._constructor(value)
        except TypeError as e:
            raise ex.SerializeException(str(e))

        result = self._constructor()
        for k, v in coerced.items():
            if self._keys is not None:
                k = self._keys(k)
            elif self._values is not None:
                v = self._values(k)
            result[k] = v
        return result

    def to_json(self, value):
        value = super().to_json(value)
        result = self._constructor()
        for k, v in value.items():
            if hasattr(k, 'to_json'):
                k = k.to_json()
            if hasattr(v, 'to_json'):
                v = v.to_json()
            result[k] = v
        return result

########################
# Serializable Objects #
########################

class _SerializeMeta(type):
    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        cls._fields = {}
        for base in bases:
            if hasattr(base, '_fields'):
                cls._fields.update(base._fields)
        cls._fields.update({attr: value for attr, value in attrs.items()
                                        if isinstance(value, Field)})

    def __call__(cls, *args, **kargs):
        obj = type.__call__(cls, *args, **kargs)
        # Validate existing arguments
        for attr, value in kargs.items():
            if attr not in cls._fields:
                raise ex.SerializeException('__init__() got an unexpected '
                                'keyword argument: {}'.format(attr))
            else:
                setattr(obj, attr, value)
        # Check for missing/default fields
        for attr, value in cls._fields.items():
            if attr in kargs:
                continue
            elif value.optional:
                setattr(obj, attr, value.default)
            else:
                raise ex.SerializeException('__init__() missing expected '
                                'argument {}'.format(attr))
        obj.post_instantiation()
        return obj

class Serializable(metaclass=_SerializeMeta):
    def __init__(self, *args, **kargs):
        pass

    def __setattr__(self, attr, value):
        cls = type(self)
        if attr in cls._fields:
            field = cls._fields[attr]
            if value != NoValue and not field.is_valid(value):
                value = field.coerce(value)
        super().__setattr__(attr, value)

    def post_instantiation(self):
        """Subclasses can override this method to perform post-instantiation
        work.
        """
        pass

    def to_json(self):
        cls = type(self)
        json = {}
        for attr, field in cls._fields.items():
            value = getattr(self, attr)
            if not field.optional or value != NoValue:
                json[attr] = field.to_json(value)
        return json

PK     8jDF���,6%  6%  %   client/sources/common/doctest_case.py"""Case for doctest-style Python tests."""

from client import exceptions
from client.sources.common import core
from client.sources.common import interpreter
from client.sources.common import models
from client.utils import output
from client.utils import timer
import code
import re
import textwrap
import traceback

class DoctestCase(interpreter.InterpreterCase):
    """TestCase for doctest-style Python tests."""

    code = core.String()

    PS1 = '>>> '
    PS2 = '... '

    def __init__(self, console, setup='', teardown='', **fields):
        """Constructor.

        PARAMETERS:
        input_str -- str; the input string, which will be dedented and
                     split along newlines.
        outputs   -- list of TestCaseAnswers
        test      -- Test or None; the test to which this test case
                     belongs.
        frame     -- dict; the environment in which the test case will
                     be executed.
        teardown  -- str; the teardown code. This code will be executed
                     regardless of errors.
        status    -- keyword arguments; statuses for the test case.
        """
        assert isinstance(console, PythonConsole), 'Improper console: {}'.format(console)
        super().__init__(console, **fields)
        self.setup = setup
        self.teardown = teardown

    def post_instantiation(self):
        self.code = textwrap.dedent(self.code)
        self.setup = textwrap.dedent(self.setup)
        self.teardown = textwrap.dedent(self.teardown)

        self.lines = _split_code(self.code, self.PS1, self.PS2)

    def preprocess(self):
        self.console.load(self.code, setup=self.setup, teardown=self.teardown)

    def lock(self, hash_fn):
        assert self.locked != False, 'called lock when self.lock = False'
        for line in self.lines:
            if isinstance(line, _Answer) and not line.locked:
                line.output = [hash_fn(output) for output in line.output]
                line.locked = True
        self.locked = True
        self._sync_code()

    def unlock(self, interact):
        """Unlocks the DoctestCase.

        PARAMETERS:
        interact -- function; handles user interaction during the unlocking
                    phase.
        """
        try:
            for line in self.lines:
                if isinstance(line, str) and line:
                    print(line)
                elif isinstance(line, _Answer):
                    if not line.locked:
                        print('\n'.join(line.output))
                        continue
                    line.output = interact(line.output, line.choices)
                    line.locked = False
            self.locked = False
        finally:
            self._sync_code()

    def _sync_code(self):
        new_code = []
        for line in self.lines:
            if isinstance(line, _Answer):
                new_code.append(line.dump())
            else:
                new_code.append(line)
        self.code = '\n'.join(new_code)

class _Answer(object):
    status_re = re.compile(r'^#\s*(.+?):\s*(.*)\s*$')
    locked_re = re.compile(r'^#\s*locked\s*$')

    def __init__(self, output=None, choices=None, explanation='', locked=False):
        self.output = output or []
        self.choices = choices or []
        self.locked = locked
        self.explanation = explanation

    def dump(self):
        result = list(self.output)
        if self.locked:
            result.append('# locked')
            if self.choices:
                for choice in self.choices:
                    result.append('# choice: ' + choice)
        if self.explanation:
            result.append('# explanation: ' + self.explanation)
        return '\n'.join(result)

    def update(self, line):
        if self.locked_re.match(line):
            self.locked = True
            return
        match = self.status_re.match(line)
        if not match:
            self.output.append(line)
        elif match.group(1) == 'locked':
            self.locked = True
        elif match.group(1) == 'explanation':
            self.explanation = match.group(2)
        elif match.group(1) == 'choice':
            self.choices.append(match.group(2))

class PythonConsole(interpreter.Console):
    PS1 = DoctestCase.PS1
    PS2 = DoctestCase.PS2

    def __init__(self, verbose, interactive, timeout=None):
        super().__init__(verbose, interactive, timeout)
        self.load('')   # Initialize empty code.

    def load(self, code, setup='', teardown=''):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.
        """
        self._frame = {}
        self._setup = textwrap.dedent(setup).split('\n')
        self._code = _split_code(code, self.PS1, self.PS2)
        self._teardown = textwrap.dedent(teardown).split('\n')

    def interpret(self):
        """Interprets the console on the loaded code.

        RETURNS:
        bool; True if the code passes, False otherwise.
        """
        try:
            self._interpret_lines(self._setup)
            self._interpret_lines(self._code, compare=True)
        except PythonConsoleException as e:
            # TODO(albert): print error details
            return False
        else:
            return True
        finally:
            self._interpret_lines(self._teardown)

    def _interpret_lines(self, lines, compare=False):
        self.clear_history()

        current = []
        for line in lines + ['']:
            if isinstance(line, str):
                if current and (line.startswith(self.PS1) or not line):
                    # Previous prompt ends when PS1 or a blank line occurs
                    self._evaluate('\n'.join(current))
                    current = []
                if line:
                    print(line)
                line = self._strip_prompt(line)
                self.add_history(line)
                current.append(line)
            elif isinstance(line, _Answer):
                assert len(current) > 0, 'Answer without a prompt'
                self._compare('\n'.join(line.output), '\n'.join(current))
                current = []

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        console = code.InteractiveConsole(self._frame)
        console.interact('# Interactive console. Type exit() to quit')

    def _compare(self, expected, code):
        try:
            value, output = self._evaluate(code)
        except PythonConsoleException as e:
            actual = e.exception.__class__.__name__
        else:
            if value is not None:
                print(repr(value))
                actual = (output + '\n' + repr(value)).strip()
            else:
                actual = output.strip()

        expected = expected.strip()
        if expected != actual:
            print()
            print('# Error: expected')
            print('\n'.join('#     {}'.format(line)
                            for line in expected.split('\n')))
            print('# but got')
            print('\n'.join('#     {}'.format(line)
                            for line in actual.split('\n')))
            raise PythonConsoleException

    def _evaluate(self, code, frame=None):
        if frame is None:
            frame = self._frame
        log_id = output.new_log()
        try:
            try:
                result = timer.timed(self.timeout, eval, (code, frame))
            except SyntaxError:
                timer.timed(self.timeout, exec, (code, frame))
                result = None
        except RuntimeError as e:
            stacktrace_length = 9
            stacktrace = traceback.format_exc().split('\n')
            print('Traceback (most recent call last):\n  ...')
            print('\n'.join(stacktrace[-stacktrace_length:-1]))
            print('# Error: maximum recursion depth exceeded.')
            raise PythonConsoleException(e)
        except exceptions.Timeout as e:
            print('# Error: evaluation exceeded {} seconds.'.format(e.timeout))
            raise PythonConsoleException(e)
        except Exception as e:
            stacktrace = traceback.format_exc()
            token = '<module>\n'
            index = stacktrace.rfind(token) + len(token)
            stacktrace = stacktrace[index:].rstrip('\n')
            if '\n' in stacktrace:
                print('Traceback (most recent call last):')
            print(stacktrace)
            raise PythonConsoleException(e)
        else:
            printed_output = ''.join(output.get_log(log_id))
            return result, printed_output
        finally:
            output.remove_log(log_id)

    def _strip_prompt(self, line):
        if line.startswith(self.PS1):
            return line[len(self.PS1):]
        elif line.startswith(self.PS2):
            return line[len(self.PS2):]
        return line

class PythonConsoleException(Exception):
    def __init__(self, exception=None):
        self.exception = exception


def _split_code(code, PS1, PS2):
    processed_lines = []
    for line in textwrap.dedent(code).split('\n'):
        if not line or line.startswith(PS1) or line.startswith(PS2):
            processed_lines.append(line)
            continue

        assert len(processed_lines) > 0, 'code improperly formated: {}'.format(code)
        if not isinstance(processed_lines[-1], _Answer):
            processed_lines.append(_Answer())
        processed_lines[-1].update(line)
    return processed_lines

PK     8jDF�;l�  �  "   client/sources/common/importing.pyimport importlib
import os

def load_module(filepath):
    module_name = path_to_module_string(filepath)
    return importlib.import_module(module_name)

def path_to_module_string(filepath):
    filepath = filepath.replace('.py', '')
    module_components = []
    while filepath:
        filepath, component = os.path.split(filepath)
        module_components.insert(0, component)
    return '.'.join(module_components)
PK     8jDF��5t�  �  $   client/sources/common/interpreter.py"""Case for generic interpreter-style tests."""

from client.sources.common import models

# TODO(albert): come up with a better cross-platform readline solution.
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

class InterpreterCase(models.Case):
    """TestCase for doctest-style Python tests."""

    def __init__(self, console, **fields):
        """Constructor.

        PARAMETERS:
        input_str -- str; the input string, which will be dedented and
                     split along newlines.
        outputs   -- list of TestCaseAnswers
        test      -- Test or None; the test to which this test case
                     belongs.
        frame     -- dict; the environment in which the test case will
                     be executed.
        teardown  -- str; the teardown code. This code will be executed
                     regardless of errors.
        status    -- keyword arguments; statuses for the test case.
        """
        super().__init__(**fields)
        self.console = console

    def run(self):
        """Implements the GradedTestCase interface."""
        self.preprocess()
        success = self.console.interpret()
        self.postprocess()
        return success

    def preprocess(self):
        pass

    def postprocess(self):
        pass

class Console(object):
    def __init__(self, verbose, interactive, timeout=None):
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

    def load(self, code, setup=None, teardown=None):
        """Prepares a set of setup, test, and teardown code to be
        run in the console.
        """
        pass

    def interpret(self):
        """Interprets the console on the loaded code.

        RETURNS:
        bool; True if the code passes, False otherwise.
        """
        raise NotImplementedError

    def interact(self):
        """Opens up an interactive session with the current state of
        the console.
        """
        pass

    ######################
    # History management #
    ######################

    def add_history(self, line):
        if HAS_READLINE:
            readline.add_history(line)

    def clear_history(self):
        if HAS_READLINE:
            readline.clear_history()
PK     8jDF�a�~�  �  "   client/sources/ok_test/__init__.pyfrom client import exceptions as ex
from client.sources.ok_test import concept
from client.sources.ok_test import doctest
from client.sources.ok_test import models
from client.sources.common import importing
import logging
import os

log = logging.getLogger(__name__)

SUITES = {
    'doctest': doctest.DoctestSuite,
    'concept': concept.ConceptSuite,
}

def load(file, parameter, args):
    """Loads an OK-style test from a specified filepath.

    PARAMETERS:
    file -- str; a filepath to a Python module containing OK-style
            tests.

    RETURNS:
    Test
    """
    filename, ext = os.path.splitext(file)
    if not os.path.isfile(file) or ext != '.py':
        log.info('Cannot import {} as an OK test'.format(file))
        raise ex.LoadingException('Cannot import {} as an OK test'.format(file))

    test = importing.load_module(file).test
    name = os.path.basename(filename)
    try:
        return {name: models.OkTest(file, SUITES, args.verbose, args.interactive,
                             args.timeout, **test)}
    except ex.SerializeException:
        raise ex.LoadingException('Cannot load OK test {}'.format(file))

PK     8jDF�'P�        client/sources/ok_test/models.pyfrom client import exceptions as ex
from client.sources.common import core
from client.sources.common import models
from client.utils import format
from client.utils import output

##########
# Models #
##########

class OkTest(models.Test):
    suites = core.List()
    description = core.String(optional=True)

    def __init__(self, file, suite_map, verbose, interactive, timeout=None, **fields):
        super().__init__(**fields)
        self.file = file
        self.suite_map = suite_map
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

    def post_instantiation(self):
        for i, suite in enumerate(self.suites):
            if not isinstance(suite, dict):
                raise ex.SerializeException('Test cases must be dictionaries')
            elif 'type' not in suite:
                raise ex.SerializeException('Suites must have field "type"')
            elif suite['type'] not in self.suite_map:
                raise ex.SerializeException('Invalid suite type: '
                                            '{}'.format(suite['type']))
            self.suites[i] = self.suite_map[suite['type']](
                    self.verbose, self.interactive, self.timeout, **suite)

    def run(self):
        """Runs the suites associated with this OK test.

        RETURNS:
        dict; the results for this test, in the form
        {
            'passed': int,
            'failed': int,
            'locked': int,
        }
        """
        passed, failed, locked = 0, 0, 0
        for i, suite in enumerate(self.suites):
            results = suite.run(self.name, i + 1)

            passed += results['passed']
            failed += results['failed']
            locked += results['locked']

        format.print_progress_bar(self.name, passed, failed, locked)
        if locked > 0:
            print()
            print('There are still locked tests! '
                  'Use the -u option to unlock them')

        if type(self.description) == str and self.description:
            print()
            print(self.description)
        print()
        return {
            'passed': passed,
            'failed': failed,
            'locked': locked,
        }

    def score(self):
        """Runs test cases and computes the score for this particular test.

        Scores are determined by aggregating results from suite.run() for each
        suite. A suite is considered passed only if it results in no locked
        nor failed results.

        The points available for this test are distributed evenly across
        scoreable (i.e. unlocked and 'scored' = True) suites.
        """
        passed, total = 0, 0
        for i, suite in enumerate(self.suites):
            if not suite.scored:
                continue

            total += 1
            results = suite.run(self.name, i + 1)

            if results['locked'] == 0 and results['failed'] == 0:
                passed += 1
        if total > 0:
            score = passed * self.points / total
        else:
            score = 0.0

        format.print_progress_bar(self.name, passed, total - passed, 0)
        print()
        return score

    def unlock(self, interact):
        total_cases = len([case for suite in self.suites
                                for case in suite.cases])
        for suite_num, suite in enumerate(self.suites):
            for case_num, case in enumerate(suite.cases):
                format.print_line('-')
                print('{} > Suite {} > Case {}'.format(self.name, suite_num + 1,
                                                       case_num + 1))
                print('(cases remaining: {})'.format(total_cases))
                print()
                total_cases -= 1

                if case.locked != True:
                    print('-- Already unlocked --')
                    print()
                    continue

                case.unlock(interact)

        assert total_cases == 0, 'Number of cases is incorrect'
        format.print_line('-')
        print('OK! All cases for {} unlocked.'.format(self.name))
        print()

    def lock(self, hash_fn):
        format.print_line('-')
        print(self.name)

        for suite_num, suite in enumerate(list(self.suites)):
            for case_num, case in enumerate(list(suite.cases)):
                message = '* Suite {} > Case {}: '.format(suite_num, case_num)
                if case.hidden:
                    suite.cases.remove(case)
                    print(message + 'removing hidden case')
                elif case.locked == core.NoValue:
                    case.lock(hash_fn)
                    print(message + 'locking')
                elif case.locked == False:
                    print(message + 'leaving unlocked')
                elif case.locked == True:
                    print(message + 'already unlocked')
        print()

    def dump(self):
        # TODO(albert): add log messages
        # TODO(albert): writing causes an error halfway, the tests
        # directory may be left in a corrupted state.
        # TODO(albert): might need to delete obsolete test files too.
        json = format.prettyjson(self.to_json())
        with open(self.file, 'w') as f:
            f.write('test = ' + json)


class Suite(core.Serializable):
    type = core.String()
    scored = core.Boolean(default=True)

    def __init__(self, verbose, interactive, timeout=None,
                 **fields):
        super().__init__(**fields)
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

    def run(self, test_name, suite_number):
        """Subclasses should override this method to run tests.

        PARAMETERS:
        test_name    -- str; name of the parent test.
        suite_number -- int; suite number, assumed to be 1-indexed.

        RETURNS:
        dict; results of the following form:
        {
            'passed': int,
            'failed': int,
            'locked': int,
        }
        """
        raise NotImplementedError

    def _run_case(self, test_name, suite_number, case, case_number):
        """A wrapper for case.run().

        Prints informative output and also captures output of the test case
        and returns it as a log. The output is suppressed -- it is up to the
        calling function to decide whether or not to print the log.
        """
        output.off()    # Delay printing until case status is determined.
        log_id = output.new_log()

        format.print_line('-')
        print('{} > Suite {} > Case {}'.format(test_name, suite_number,
                                               case_number))
        print()

        success = case.run()
        if success:
            print('-- OK! --')

        output.on()
        output_log = output.get_log(log_id)
        output.remove_log(log_id)

        return success, output_log

PK     8jDF�N9|	  |	  !   client/sources/ok_test/doctest.pyfrom client import exceptions as ex
from client.sources.common import core
from client.sources.common import doctest_case
from client.sources.ok_test import models
from client.utils import format
import logging

log = logging.getLogger(__name__)

class DoctestSuite(models.Suite):

    cases = core.List()
    setup = core.String(default='')
    teardown = core.String(default='')

    def __init__(self, verbose, interactive, timeout=None, **fields):
        super().__init__(verbose, interactive, timeout, **fields)
        self.console = doctest_case.PythonConsole(verbose, interactive, timeout)

    def post_instantiation(self):
        for i, case in enumerate(self.cases):
            if not isinstance(case, dict):
                raise ex.SerializeException('Test cases must be dictionaries')
            self.cases[i] = doctest_case.DoctestCase(self.console, self.setup,
                                                     self.teardown, **case)

    def run(self, test_name, suite_number):
        """Runs test for the doctest suite.

        PARAMETERS:
        test_name    -- str; the name of the parent test. Used for printing
                     purposes.
        suite_number -- int; the suite number in relation to the parent test.
                     Used for printing purposes.

        RETURNS:
        dict; results of the following form:
        {
            'passed': int,
            'failed': int,
            'locked': int,
        }
        """
        results = {
            'passed': 0,
            'failed': 0,
            'locked': 0,
        }
        for i, case in enumerate(self.cases):
            log.info('Running case {}'.format(i))

            if case.locked == True or results['locked'] > 0:
                # If a test case is locked, refuse to run any of the subsequent
                # test cases
                log.info('Case {} is locked'.format(i))
                results['locked'] += 1
                continue

            success, output_log = self._run_case(test_name, suite_number,
                                                 case, i + 1)

            if not success or self.verbose:
                print(''.join(output_log))

            if not success and self.interactive:
                self.console.interact()

            if success:
                results['passed'] += 1
            else:
                results['failed'] += 1
        return results
PK     8jDF�mB�    !   client/sources/ok_test/concept.py"""Case for conceptual tests.

ConceptCases are designed to be natural language tests that help
students understand high-level understanding. As such, these test cases
focus mainly on unlocking.
"""

from client import exceptions as ex
from client.sources.common import models as common_models
from client.sources.ok_test import models as ok_models
from client.sources.common import core
import textwrap
import logging

log = logging.getLogger(__name__)

class ConceptSuite(ok_models.Suite):
    scored = core.Boolean(default=False)
    cases = core.List()

    def post_instantiation(self):
        for i, case in enumerate(self.cases):
            if not isinstance(case, dict):
                raise ex.SerializeException('Test cases must be dictionaries')
            self.cases[i] = ConceptCase(**case)

    def run(self, test_name, suite_number):
        results = {
            'passed': 0,
            'failed': 0,
            'locked': 0,
        }
        for i, case in enumerate(self.cases):
            if case.locked == True or results['locked'] > 0:
                # If a test case is locked, refuse to run any of the subsequent
                # test cases
                log.info('Case {} is locked'.format(i))
                results['locked'] += 1
                continue

            success, output_log = self._run_case(test_name, suite_number,
                                                 case, i + 1)
            assert success, 'Concept case should never fail while grading'
            results['passed'] += 1

            if self.verbose:
                print(''.join(output_log))
        return results

class ConceptCase(common_models.Case):
    question = core.String()
    answer = core.String()
    choices = core.List(type=str, optional=True)

    def post_instantiation(self):
        self.question = textwrap.dedent(self.question).strip()
        self.answer = textwrap.dedent(self.answer).strip()

        if self.choices != core.NoValue:
            for i, choice in enumerate(self.choices):
                self.choices[i] = textwrap.dedent(choice).strip()

    def run(self):
        """Runs the conceptual test case.

        RETURNS:
        bool; True if the test case passes, False otherwise.
        """
        print('Q: ' + self.question)
        print('A: ' + self.answer)
        return True

    def lock(self, hash_fn):
        self.answer = hash_fn(self.answer)
        self.locked = True

    def unlock(self, interact):
        """Unlocks the conceptual test case."""
        print('Q: ' + self.question)
        answer = interact([self.answer], self.choices)
        assert len(answer) == 1
        answer = answer[0]
        if answer != self.answer:
            # Answer was presumably unlocked
            self.locked = False
            self.answer = answer

PK     8jDF��p��	  �	  "   client/sources/doctest/__init__.pyfrom client import exceptions as ex
from client.sources.common import importing
from client.sources.doctest import models
import logging
import os
import traceback

log = logging.getLogger(__name__)

def load(file, name, args):
    """Loads doctests from a specified filepath.

    PARAMETERS:
    file -- str; a filepath to a Python module containing OK-style
            tests.
    name -- str; optional parameter that specifies a particular function in
            the file. If omitted, all doctests will be included.

    RETURNS:
    Test
    """
    if not os.path.isfile(file) or not file.endswith('.py'):
        log.info('Cannot import doctests from {}'.format(file))
        raise ex.LoadingException('Cannot import doctests from {}'.format(file))

    try:
        module = importing.load_module(file)
    except Exception:
        # Assume that part of the traceback includes frames from importlib.
        # Begin printing the traceback after the last line involving importlib.
        # TODO(albert): Try to find a cleaner way to do this. Also, might want
        # to move this to a more general place.
        print('Traceback (most recent call last):')
        stacktrace = traceback.format_exc().split('\n')
        start = 0
        for i, line in enumerate(stacktrace):
            if 'importlib' in line:
                start = i + 1
        print('\n'.join(stacktrace[start:]))

        raise ex.LoadingException('Error importing file {}'.format(file))

    if name:
        return {name: _load_test(file, module, name, args)}
    else:
        return _load_tests(file, module, args)


def _load_tests(file, module, args):
    tests = {}
    for name in dir(module):
        if callable(getattr(module, name)):
            tests[name] = _load_test(file, module, name, args)
    return tests

def _load_test(file, module, name, args):
    if not hasattr(module, name):
        raise ex.LoadingException('Module {} has no function {}'.format(
                                  module.__name__, name))
    func = getattr(module, name)
    if not callable(func):
        raise ex.LoadingException('Attribute {} is not a function'.format(name))

    docstring = func.__doc__ if func.__doc__ else ''
    try:
        return models.Doctest(file, args.verbose, args.interactive, args.timeout,
                              name=name, points=1, docstring=docstring)
    except ex.SerializeException:
        raise ex.LoadingException('Unable to load doctest for {} '
                                  'from {}'.format(name, file))

PK     8jDFߟ�
o  o      client/sources/doctest/models.pyfrom client import exceptions as ex
from client.sources.common import core
from client.sources.common import models
from client.sources.common import doctest_case
from client.sources.common import importing
from client.utils import format
from client.utils import output
import re
import textwrap

##########
# Models #
##########

class Doctest(models.Test):
    docstring = core.String()

    PS1 = '>>> '
    PS2 = '... '

    SETUP = PS1 + 'from {} import *'
    prompt_re = re.compile(r'(\s*)({}|{})'.format(PS1, '\.\.\. '))

    def __init__(self, file, verbose, interactive, timeout=None, **fields):
        super().__init__(**fields)
        self.file = file
        self.verbose = verbose
        self.interactive = interactive
        self.timeout = timeout

        self.console = doctest_case.PythonConsole(self.verbose, self.interactive,
                                                  self.timeout)

    def post_instantiation(self):
        # TODO(albert): rewrite test validation. Inconsistent leading space is
        # currently not validated correctly (see tests).
        self.docstring = textwrap.dedent(self.docstring)
        code = []
        prompt_on = False
        leading_space = ''
        for line in self.docstring.split('\n'):
            prompt_match = self.prompt_re.match(line)
            if prompt_match:
                if prompt_on and not line.startswith(leading_space):
                    raise ex.SerializeException('Inconsistent tabs for doctest')
                elif not prompt_on:
                    prompt_on = True
                    leading_space = prompt_match.group(1)
                code.append(line.lstrip())
            elif not line.strip():
                prompt_on = False
                leading_space = ''
            elif prompt_on:
                if not line.startswith(leading_space):
                    raise ex.SerializeException('Inconsistent tabs for doctest')
                code.append(line.lstrip())
        module = self.SETUP.format(importing.path_to_module_string(self.file))
        self.case = doctest_case.DoctestCase(self.console, module,
                                             code='\n'.join(code))

    def run(self):
        """Runs the suites associated with this doctest.

        RETURNS:
        bool; True if the doctest completely passes, False otherwise.
        """
        output.off()
        log_id = output.new_log()

        format.print_line('-')
        print('Doctests for {}'.format(self.name))
        print()

        if not self.docstring:
            print('-- No doctests found for {} --'.format(self.name))
            success = False
        else:
            success = self.case.run()
            if success:
                print('-- OK! --')

        output.on()
        output_log = output.get_log(log_id)
        output.remove_log(log_id)

        if not success or self.verbose:
            print(''.join(output_log))

        if not success and self.interactive:
            self.console.interact()

        if success:
            return {'passed': 1, 'failed': 0, 'locked': 0}
        else:
            return {'passed': 0, 'failed': 1, 'locked': 0}

    def score(self):
        format.print_line('-')
        print('Doctests for {}'.format(self.name))
        print()
        success = self.case.run()
        score = 1.0 if success else 0.0

        print('Score: {}/1'.format(score))
        print()
        return score

    def unlock(self, interact):
        """Doctests cannot be unlocked."""

    def lock(self, hash_fn):
        """Doctests cannot be locked."""

    def dump(self):
        """Doctests do not need to be dumped, since no state changes."""
PK     8jDF���`  `     client/protocols/unlock.py"""Implements the UnlockProtocol, which unlocks all specified tests
associated with an assignment.

The UnlockTestCase interface can be implemented by TestCases that are
compatible with the UnlockProtocol.
"""

from client.protocols.common import models
from client.utils import format
import hmac
import logging
import random
import string

log = logging.getLogger(__name__)

try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

class UnlockProtocol(models.Protocol):
    """Unlocking protocol that wraps that mechanism."""

    PROMPT = '? '       # Prompt that is used for user input.
    EXIT_INPUTS = (     # Valid user inputs for aborting the session.
        'exit()',
        'quit()',
    )

    def __init__(self, cmd_args, assignment):
        super().__init__(cmd_args, assignment)
        self.hash_key = assignment.name

    def on_interact(self):
        """Responsible for unlocking each test.

        The unlocking process can be aborted by raising a KeyboardInterrupt or
        an EOFError.

        RETURNS:
        dict; mapping of test name (str) -> JSON-serializable object. It is up
        to each test to determine what information is significant for analytics.
        """
        if not self.args.unlock:
            return

        format.print_line('~')
        print('Unlocking tests')
        print()

        print('At each "{}", type what you would expect the output to be.'.format(
              self.PROMPT))
        print('Type {} to quit'.format(self.EXIT_INPUTS[0]))
        print()

        analytics = {}
        for test in self.assignment.specified_tests:
            log.info('Unlocking test {}'.format(test.name))
            try:
                analytics[test.name] = test.unlock(self.interact)
            except (KeyboardInterrupt, EOFError):
                try:
                    # TODO(albert): When you use Ctrl+C in Windows, it
                    # throws two exceptions, so you need to catch both
                    # of them. Find a cleaner fix for this.
                    print()
                    print('-- Exiting unlocker --')
                except (KeyboardInterrupt, EOFError):
                    pass
                print()
                break
        return analytics

    def interact(self, answer, choices=None, randomize=True):
        """Reads student input for unlocking tests until the student
        answers correctly.

        PARAMETERS:
        answer    -- list; a list of locked lines in a test case answer.
        choices   -- list or None; a list of choices. If None or an
                     empty list, signifies the question is not multiple
                     choice.

        DESCRIPTION:
        Continually prompt the student for an answer to an unlocking
        question until one of the folliwng happens:

            1. The student supplies the correct answer, in which case
               the supplied answer is returned
            2. The student aborts abnormally (either by typing 'exit()'
               or using Ctrl-C/D. In this case, return None

        Correctness is determined by the verify method.

        RETURNS:
        list; the correct solution (that the student supplied). Each element
        in the list is a line of the correct output.
        """
        # attempts = 0
        if randomize and choices:
            choices = random.sample(choices, len(choices))
        correct = False
        while not correct:
            # attempts += 1
            if choices:
                assert len(answer) == 1, 'Choices must have 1 line of output'
                choice_map = self._display_choices(choices)

            input_lines = []
            for i in range(len(answer)):
                if len(answer) == 1:
                    prompt = self.PROMPT
                else:
                    prompt = '(line {}){}'.format(i + 1, self.PROMPT)

                student_input = format.normalize(self._input(prompt))
                self._add_history(student_input)
                if student_input in self.EXIT_INPUTS:
                    raise EOFError

                if choices and student_input in choice_map:
                    student_input = choice_map[student_input]

                if not self._verify(student_input, answer[i]):
                    break
                else:
                    input_lines.append(student_input)
            else:
                correct = True


            # TODO(albert): record analytis
            # Performt his before the function exits?
            # self._analytics[self._analytics['current']].append((attempts, correct))

            # if input_lines.lower() in self.EXIT_INPUTS:
            #     attempts -= 1
            #     self._analytics[self._analytics['current']].append((attempts, correct))
            #     return

            if not correct:
                print("-- Not quite. Try again! --")
            else:
                print("-- OK! --")
            print()
        # self._analytics[self._analytics['current']].append((attempts, correct))
        return input_lines

    ###################
    # Private Methods #
    ###################

    def _verify(self, guess, locked):
        return hmac.new(self.hash_key.encode('utf-8'),
                        guess.encode('utf-8')).hexdigest() == locked

    def _input(self, prompt):
        """Retrieves user input from stdin."""
        return input(prompt)

    def _display_choices(self, choices):
        """Prints a mapping of numbers to choices and returns the
        mapping as a dictionary.
        """
        print("Choose the number of the correct choice:")
        choice_map = {}
        # TODO(albert): consider using letters as choices instead of numbers.
        for i, choice in enumerate(choices):
            print('    {}) {}'.format(i, choice))
            i = str(i)
            choice = format.normalize(choice)
            choice_map[i] = choice
        return choice_map

    def _add_history(self, line):
        """Adds the given line to readline history, only if the line
        is non-empty.
        """
        if line and HAS_READLINE:
            readline.add_history(line)

protocol = UnlockProtocol
PK     8jDF               client/protocols/__init__.pyPK     8jDF��`�       client/protocols/scoring.py"""Implements the ScoringProtocol, which runs all specified tests
associated with an assignment.
"""

from client.sources.common import core
from client.sources.common import models as sources_models
from client.protocols.common import models as protocol_models
from client.utils import format
from collections import OrderedDict
import logging

log = logging.getLogger(__name__)

#####################
# Testing Mechanism #
#####################

class ScoringProtocol(protocol_models.Protocol):
    """A Protocol that runs tests, formats results, and reports a
    student's score.
    """
    def on_interact(self):
        """Score tests and print results

        Tests are taken from self.assignment.specified_tests. Each test belongs
        to a partner. If test.partner is omitted (i.e. core.NoValue), the score
        for that test is added to every partner's score.

        RETURNS
        dict; mapping of partner (int) -> finalized scores (float).

        If there are no tests, the mapping will only contain one entry, mapping
        (partner) 0 -> 0 (total score).

        If there are no partners specified by the tests, the mapping will only
        contain one entry, mapping (partner) 0 -> total score (float). This
        assumes there is always at least one partner.
        """
        if not self.args.score:
            return

        format.print_line('~')
        print('Scoring tests')
        print()

        raw_scores = OrderedDict()
        for test in self.assignment.specified_tests:
            assert isinstance(test, sources_models.Test), 'ScoringProtocol received invalid test'

            log.info('Scoring test {}'.format(test.name))
            partner = test.partner if test.partner != core.NoValue else None
            raw_scores[test.name, partner] = (test.score(), test.points)

        return display_breakdown(raw_scores)

def display_breakdown(scores):
    """Prints the point breakdown given a dictionary of scores.

    RETURNS:
    dict; maps partner (int) -> finalized score (float)
    """
    partner_totals = {}

    format.print_line('-')
    print('Point breakdown')
    for (name, partner), (score, total) in scores.items():
        print('    {}: {}/{}'.format(name, score, total))
        partner_totals[partner] = partner_totals.get(partner, 0) + score
    print()

    shared_points = partner_totals.get(None, 0)
    if None in partner_totals:
        del partner_totals[None]

    finalized_scores = {}
    print('Score')
    if len(partner_totals) == 0:
        # Add partner 0 as only partner.
        partner_totals[0] = 0
    for partner, score in sorted(partner_totals.items()):
        print('    Partner {}: {}'.format(partner, score + shared_points))
        finalized_scores[partner] = score + shared_points
    return finalized_scores

protocol = ScoringProtocol
PK     8jDF�h��V  V     client/protocols/grading.py"""Implements the GradingProtocol, which runs all specified tests
associated with an assignment.

The GradedTestCase interface should be implemented by TestCases that
are compatible with the GradingProtocol.
"""

from client.protocols.common import models
from client.utils import format
import logging

log = logging.getLogger(__name__)

#####################
# Testing Mechanism #
#####################

class GradingProtocol(models.Protocol):
    """A Protocol that runs tests, formats results, and sends results
    to the server.
    """
    def on_interact(self):
        """Run gradeable tests and print results and return analytics.

        RETURNS:
        dict; a mapping of test name -> JSON-serializable object. It is up to
        each test to determine what kind of data it wants to return as
        significant for analytics. However, all tests must include the number
        passed, the number of locked tests and the number of failed tests.
        """
        if self.args.score:
            return

        format.print_line('~')
        print('Running tests')
        print()
        passed = 0
        failed = 0
        locked = 0

        analytics = {}

        for test in self.assignment.specified_tests:
            log.info('Running tests for {}'.format(test.name))
            results = test.run()

            passed += results['passed']
            failed += results['failed']
            locked += results['locked']
            analytics[test.name] = results

        format.print_progress_bar('Test summary', passed, failed, locked)
        return analytics

protocol = GradingProtocol
PK     8jDF^Đ+  +     client/protocols/lock.pyfrom client.protocols.common import models
from client.utils import format
import hmac
import logging

log = logging.getLogger(__name__)

class LockProtocol(models.Protocol):
    """Locking protocol that wraps that mechanism."""

    name = 'lock'

    def on_start(self):
        """Responsible for locking each test."""
        if not self.args.lock:
            return

        format.print_line('~')
        print('Locking tests')
        print()

        for test in self.assignment.test_map.values():
            log.info('Locking {}'.format(test.name))
            test.lock(self._hash_fn)

    def _hash_fn(self, text):
        text = format.normalize(text)
        return hmac.new(self.assignment.name.encode('utf-8'),
                        text.encode('utf-8')).hexdigest()

protocol = LockProtocol
PK     8jDFZ/l�  �  !   client/protocols/file_contents.pyfrom client.protocols.common import models
import logging
import os

log = logging.getLogger(__name__)

# TODO(albert): rename this file to backup.py. Leaving it as file_contents.py
# for now because server isn't ready for a change yet.

class BackupProtocol(models.Protocol):
    """The contents of source files are sent to the server."""

    def on_start(self):
        """Find all source files and return their complete contents.

        Source files are considered to be files listed self.assignment.src.
        If a certain source filepath is not a valid file (e.g. does not exist
        or is not a file), then the contents associated with that filepath will
        be an empty string.

        RETURNS:
        dict; a mapping of source filepath -> contents as strings.
        """
        files = {}
        # TODO(albert): move this to AnalyticsProtocol
        if self.args.submit:
            files['submit'] = True
        for file in self.assignment.src:
            if not self.is_file(file):
                # TODO(albert): add an error message
                contents = ''
                log.warning('File {} does not exist'.format(file))
            else:
                contents = self.read_file(file)
                log.info('Loaded contents of {} to send to server'.format(file))
            files[file] = contents
        return files

    #####################
    # Mockable by tests #
    #####################

    def is_file(self, filepath):
        return os.path.isfile(filepath)

    def read_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as lines:
            return lines.read()

protocol = BackupProtocol
PK     8jDFئ�V  V     client/protocols/analytics.py"""Implements the AnalyticsProtocol, which keeps track of configuration
for the ok grading session.
"""

from client.protocols.common import models
from datetime import datetime

# TODO(albert): rename this InformationProtocol
# Add all command line arguments here

class AnalyticsProtocol(models.Protocol):
    """A Protocol that analyzes how much students are using the autograder.
    """
    name = 'analytics'

    def on_start(self):
        """
        Returns some analytics about this autograder run.
        """
        statistics = {}
        statistics['time'] = str(datetime.now())
        statistics['unlock'] = self.args.unlock

        if self.args.question:
            # TODO(denero) Get the canonical name of the question
            statistics['question'] = self.args.question

        return statistics

protocol = AnalyticsProtocol
PK     8jDF            #   client/protocols/common/__init__.pyPK     8jDF:��  �  !   client/protocols/common/models.pyfrom client import exceptions

class Protocol(object):
    """A Protocol encapsulates a single aspect of ok.py functionality."""
    def __init__(self, cmd_line_args, assignment):
        """Constructor.

        PARAMETERS:
        cmd_line_args -- Namespace; parsed command line arguments.
                         command line, as parsed by argparse.
        assignment    -- dict; general information about the assignment.
        """
        self.args = cmd_line_args
        self.assignment = assignment

    def on_start(self):
        """Called when ok.py starts. Returns an object to be sent to server."""

    def on_interact(self):
        """Called to execute an interactive or output-intensive session."""

PK     \kDF               client/cli/__init__.pyPK     \kDFyH�h!  !     client/cli/ok.py"""The ok.py script runs tests, checks for updates, and saves your work.

Common uses:
  python3 ok.py          Run unlocked tests (and save your work).
  python3 ok.py -u       Unlock new tests interactively.
  python3 ok.py -h       Display full help documentation.

This script will search the current directory for test files. Make sure that
ok.py appears in the same directory as the assignment you wish to test.
Otherwise, use -t to specify a test file manually.
"""

# TODO(denero) Add mechanism for removing DEVELOPER INSTRUCTIONS.
DEVELOPER_INSTRUCTIONS = """

This multi-line string contains instructions for developers. It is removed
when the client is distributed to students.

This file is responsible for coordinating all communication with the ok-server.
Students should never need to modify this file.

Local and remote interactions are encapsulated as protocols.
Contributors should do the following to add a protocol to this autograder:

    1- Extend the Protocol class and implement on_start and on_interact.
    2- Add the classname of your protocol to the "protocols" list.
    3- If your protocol needs command line arguments, change parse_input.

A standard protocol lifecycle has only one round-trip communication with the
server, processed by the on_start method. If other interactions are required
outside of this lifecycle, the send_to_server function can be used to send and
receive information from the server outside of the default times. Such
communications should be limited to the body of an on_interact method.
"""
from client import exceptions as ex
from client.cli.common import assignment
from client.utils import auth
from client.utils import network
from client.utils import output
from datetime import datetime
from urllib import error
import argparse
import client
import logging
import os
import pickle
import sys

LOGGING_FORMAT = '%(levelname)s | pid %(process)d | %(filename)s:%(lineno)d | %(message)s'
logging.basicConfig(format=LOGGING_FORMAT)
log = logging.getLogger('client')   # Get top-level logger

CLIENT_ROOT = os.path.dirname(client.__file__)
BACKUP_FILE = ".ok_messages"

##########################
# Command-line Interface #
##########################

def parse_input():
    """Parses command line input."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # Protocol paramters
    parser.add_argument('-q', '--question', type=str, action='append',
                        help="focus on specific questions")
    parser.add_argument('-u', '--unlock', action='store_true',
                        help="unlock tests interactively")
    parser.add_argument('-i', '--interactive', action='store_true',
                        help="toggle interactive mode")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="print more output")
    parser.add_argument('--submit', action='store_true',
                        help="wait for server response without timeout")
    parser.add_argument('--lock', action='store_true',
                        help="partial path to directory to lock")
    parser.add_argument('--score', action='store_true',
                        help="Scores the assignment")
    parser.add_argument('--config', type=str,
                        help="Specify a configuration file")
    parser.add_argument('--timeout', type=int, default=10,
                        help="set the timeout duration for running tests")

    # Debug information
    parser.add_argument('--version', action='store_true',
                        help="Prints the version number and quits")
    parser.add_argument('--tests', action='store_true',
                        help="display a list of all available tests")
    parser.add_argument('--debug', action='store_true',
                        help="show debug statements")

    # Server parameters
    parser.add_argument('--local', action='store_true',
                        help="disable any network activity")
    parser.add_argument('--server', type=str,
                        default='ok-server.appspot.com',
                        help="server address")
    parser.add_argument('--authenticate', action='store_true',
                        help="authenticate, ignoring previous authentication")
    parser.add_argument('--insecure', action='store_true',
                        help="uses http instead of https")

    return parser.parse_args()

def main():
    """Run all relevant aspects of ok.py."""
    args = parse_input()

    log.setLevel(logging.DEBUG if args.debug else logging.ERROR)
    log.debug(args)

    if args.version:
        print("okpy=={}".format(client.__version__))
        exit(0)

    # Instantiating assignment
    try:
        assign = assignment.load_config(args.config, args)
    except (ex.LoadingException, ex.SerializeException) as e:
        log.warning('Assignment could not instantiate', exc_info=True)
        print('Error: ' + str(e).strip())
        exit(1)

    # Load backup files
    msg_list = []
    try:
        with open(BACKUP_FILE, 'rb') as fp:
            msg_list = pickle.load(fp)
            log.info('Loaded %d backed up messages from %s',
                     len(msg_list), BACKUP_FILE)
    except (IOError, EOFError) as e:
        log.info('Error reading from ' + BACKUP_FILE \
                + ', assume nothing backed up')
    except KeyboardInterrupt:
        log.warning('Backup messages were not loaded due to KeyboardInterrupt')


    try:
        # Load tests and protocols
        assign.load()

        if args.tests:
            print('Available tests:')
            for name in assign.test_map:
                print('    ' + name)
            exit(0)

        # Run protocol.on_start
        start_messages = dict()
        for name, proto in assign.protocol_map.items():
            log.info('Execute {}.on_start()'.format(name))
            start_messages[name] = proto.on_start()
        # TODO(albert): doesn't AnalyticsProtocol store the timestamp?
        start_messages['timestamp'] = str(datetime.now())
        msg_list.append(start_messages)

        # Run protocol.on_interact
        interact_msg = {}
        for name, proto in assign.protocol_map.items():
            log.info('Execute {}.on_interact()'.format(name))
            interact_msg[name] = proto.on_interact()
        # TODO(albert): doesn't AnalyticsProtocol store the timestamp?
        interact_msg['timestamp'] = str(datetime.now())
        msg_list.append(interact_msg)
    except ex.LoadingException as e:
        log.warning('Assignment could not load', exc_info=True)
        print('Error loading assignment')
    except KeyboardInterrupt:
        log.info('Quitting protocols')
        assign.dump_tests()
    else:
        assign.dump_tests()

    if args.local:
        return

    # Send request to server
    try:
        # TODO(denero) Print server responses.

        # Check if ssl is available
        if not args.insecure:
            try:
                import ssl
            except:
                log.warning('Error importing ssl', stack_info=True)
                sys.exit("SSL Bindings are not installed. You can install python3 SSL bindings or \nrun ok locally with python3 ok --local")

        try:
            access_token = auth.authenticate(args.authenticate)
            log.info('Authenticated with access token %s', access_token)

            print("Backing up your work...")
            response = network.dump_to_server(access_token, msg_list,
                               assign.endpoint, args.server, args.insecure,
                               client.__version__, log, send_all=args.submit)

            if response:
                print("Back-up successful for user: {0}".format(response['data']['email']))
                print("URL: https://ok-server.appspot.com/#/{0}/submission/{1}".format(response['data']['course'], response['data']['key']))

        except error.URLError as e:
            log.warning('on_start messages not sent to server: %s', str(e))

        with open(BACKUP_FILE, 'wb') as fp:
            log.info('Save %d unsent messages to %s', len(msg_list),
                     BACKUP_FILE)

            pickle.dump(msg_list, fp)
            os.fsync(fp)

        if len(msg_list) == 0:
            print("Backup successful.")
    except KeyboardInterrupt:
        print("Quitting ok.")

if __name__ == '__main__':
    main()
PK     8jDF               client/cli/common/__init__.pyPK     8jDFe�L�"  "     client/cli/common/assignment.pyfrom client import exceptions as ex
from client.sources.common import core
from client.utils import format
import client
import collections
import glob
import importlib
import json
import logging
import os
import zipfile
import textwrap

log = logging.getLogger(__name__)

CONFIG_EXTENSION = '*.ok'

def load_config(filepath, args):
    config = get_config(filepath)
    if not isinstance(config, dict):
        raise ex.LoadingException('Config should be a dictionary')
    return Assignment(args, **config)

def get_config(config):
    if config is None:
        configs = glob.glob(CONFIG_EXTENSION)
        if len(configs) > 1:
            raise ex.LoadingException(textwrap.dedent("""
            Multiple .ok files found:
                {}

            Please specify a particular assignment's config file with
                python3 ok --config <config file>
            """.format(' '.join(configs))))
        elif not configs:
            raise ex.LoadingException('No .ok configuration file found')
        config = configs[0]

    try:
        with open(config, 'r') as f:
            result = json.load(f, object_pairs_hook=collections.OrderedDict)
    except IOError:
        raise ex.LoadingException('Error loading config: {}'.format(config))
    else:
        log.info('Loaded config from {}'.format(config))
        return result


class Assignment(core.Serializable):
    name = core.String()
    endpoint = core.String()
    src = core.List(type=str, optional=True)
    tests = core.Dict(keys=str, values=str, ordered=True)
    protocols = core.List(type=str)

    _TESTS_PACKAGE = 'client.sources'
    _PROTOCOL_PACKAGE = 'client.protocols'

    def __init__(self, cmd_args, **fields):
        self.cmd_args = cmd_args
        self.test_map = collections.OrderedDict()
        self.protocol_map = collections.OrderedDict()
        self.specified_tests = []

    def post_instantiation(self):
        self._print_header()

    def load(self):
        """Load tests and protocols."""
        self._load_tests()
        self._load_protocols()
        self._resolve_specified_tests()

    def _load_tests(self):
        """Loads all tests specified by test_map.

        PARAMETERS:
        test_map -- dict; file pattern -> serialize module. Every file that
                    that matches the UNIX style file pattern will be loaded
                    by the module.load method.
        """
        log.info('Loading tests')
        for file_pattern, source in self.tests.items():
            # Separate filepath and parameter
            if ':' in file_pattern:
                file_pattern, parameter = file_pattern.split(':', 1)
            else:
                parameter = ''

            for file in self._find_files(file_pattern):
                try:
                    module = self._import_module(self._TESTS_PACKAGE + '.' + source)
                except ImportError:
                    raise ex.LoadingException('Invalid test source: {}'.format(source))

                test_name = file
                if parameter:
                    test_name += ':' + parameter
                self.test_map.update(module.load(file, parameter, self.cmd_args))
                log.info('Loaded {}'.format(test_name))

        if not self.test_map:
            raise ex.LoadingException('No tests loaded')

    def dump_tests(self):
        """Dumps all tests, as determined by their .dump() method.

        PARAMETERS:
        tests -- dict; file -> Test. Each Test object has a .dump method
                 that takes a filename and serializes the test object.
        """
        log.info('Dumping tests')
        for test in self.test_map.values():
            try:
                test.dump()
            except ex.SerializeException as e:
                log.warning('Unable to dump {}: {}'.format(test.name, str(e)))
            else:
                log.info('Dumped {}'.format(test.name))

    def _resolve_specified_tests(self):
        """For each of the questions specified on the command line,
        find the test corresponding that question.

        Questions are preserved in the order that they are specified on the
        command line. If no questions are specified, use the entire set of
        tests.
        """
        if not self.cmd_args.question:
            log.info('Using all tests (no questions specified)')
            self.specified_tests = list(self.test_map.values())
            return
        elif not self.test_map:
            log.info('No tests loaded')
            return
        for question in self.cmd_args.question:
            if question not in self.test_map:
                print('Test "{}" not found.'.format(question))
                print('Did you mean one of the following? '
                      '(Names are case sensitive)')
                for test in self.test_map:
                    print('    {}'.format(test))
                raise ex.LoadingException('Invalid test specified: {}'.format(question))

            log.info('Adding {} to specified tests'.format(question))
            if question not in self.specified_tests:
                self.specified_tests.append(self.test_map[question])


    def _load_protocols(self):
        log.info('Loading protocols')
        for proto in self.protocols:
            try:
                module = self._import_module(self._PROTOCOL_PACKAGE + '.' + proto)
            except ImportError:
                raise ex.LoadingException('Invalid protocol: {}'.format(proto))

            self.protocol_map[proto] = module.protocol(self.cmd_args, self)
            log.info('Loaded protocol "{}"'.format(proto))

    def _print_header(self):
        format.print_line('=')
        print('Assignment: {}'.format(self.name))
        print('OK, version {}'.format(client.__version__))
        format.print_line('=')
        print()

    def _find_files(self, pattern):
        return glob.glob(pattern)

    def _import_module(self, module):
        return importlib.import_module(module)

def _has_subsequence(string, pattern):
    """Returns true if the pattern is a subsequence of string."""
    string_index, pattern_index = 0, 0
    while string_index < len(string) and pattern_index < len(pattern):
        if string[string_index] == pattern[pattern_index]:
            string_index += 1
            pattern_index += 1
        else:
            string_index += 1
    return pattern_index == len(pattern)

PK     8jDFq~��  �     client/utils/format.py"""Formatting utilities."""

from client import exceptions
import textwrap

#############
# Whtespace #
#############

def dedent(text):
    """Dedents a string of text.

    Leading whitespace that is common to all lines in the string is
    removed. Any leading newlines and trailing whitespace is also
    removed.
    """
    return textwrap.dedent(text).lstrip('\n').rstrip()

def indent(text, indentation):
    """Indents a string of text with the given string of indentation.

    PARAMETERS:
    text        -- str
    indentation -- str; prefix of indentation to add to the front of
                   every new line.

    RETURNS:
    str; the newly indented string.
    """
    return '\n'.join([indentation + line for line in text.splitlines()])

def normalize(text):
    """Normalizes whitespace in a specified string of text."""
    return " ".join(text.strip().split())

############
# Printing #
############

def print_line(style, length=69):
    """Prints an underlined version of the given line with the
    specified underline style.

    PARAMETERS:
    style  -- str; a one-character string that denotes the line style.
    length -- int; the width of the line. The default is 69, which is the width
              for doctest lines.
    """
    print(style * length)

def print_progress_bar(header, passed, failed, locked):
    print_line('-')
    print(header)
    print('    Passed: {}'.format(passed))
    print('    Failed: {}'.format(failed))
    if locked > 0:
        print('    Locked: {}'.format(locked))

    # Print [oook.....] progress bar
    total = passed + failed + locked
    percent = round(100 * passed / total, 1) if total != 0 else 0.0
    print('[{}k{}] {}% passed'.format(
        'o' * int(percent // 10),
        '.' * int(10 - (percent // 10)),
        percent))

#################
# Serialization #
#################

def prettyjson(json, indentation='  '):
    """Formats a Python-object into a string in a JSON like way, but
    uses triple quotes for multiline strings.

    PARAMETERS:
    json        -- Python object that is serializable into json.
    indentation -- str; represents one level of indentation

    NOTES:
    All multiline strings are treated as raw strings.

    RETURNS:
    str; the formatted json-like string.
    """
    if isinstance(json, int) or isinstance(json, float):
        return str(json)
    elif isinstance(json, str):
        if '\n' in json:
            return 'r"""\n' + dedent(json) + '\n"""'
        return repr(json)
    elif isinstance(json, list):
        lst = [indent(prettyjson(el, indentation), indentation) for el in json]
        return '[\n' + ',\n'.join(lst) + '\n]'
    elif isinstance(json, dict):
        pairs = []
        for k, v in sorted(json.items()):
            k = prettyjson(k, indentation)
            v = prettyjson(v, indentation)
            pairs.append(indent(k + ': ' + v, indentation))
        return '{\n' + ',\n'.join(pairs) + '\n}'
    else:
        raise exceptions.SerializeException('Invalid json type: {}'.format(json))

PK     8jDF               client/utils/__init__.pyPK     8jDFD�\O  O     client/utils/auth.py#!/usr/bin/env python3

from client.utils.sanction import Client
from urllib.parse import urlparse, parse_qs
import http.server
import pickle
import sys
import time
import webbrowser

CLIENT_ID = \
    '931757735585-vb3p8g53a442iktc4nkv5q8cbjrtuonv.apps.googleusercontent.com'
# The client secret in an installed application isn't a secret.
# See: https://developers.google.com/accounts/docs/OAuth2InstalledApp
CLIENT_SECRET = 'zGY9okExIBnompFTWcBmOZo4'
REFRESH_FILE = '.ok_refresh'
REDIRECT_HOST = "localhost"
TIMEOUT = 10

SUCCESS_HTML = """
<html>
<head>
<title>Authentication Success</title>
</head>
<body>
<b>Ok! You have successfully authenticated.</b>
</body>
</html>
"""

def pick_free_port():
    import socket
    port_guess = 7777
    while port_guess < 65535:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('localhost', port_guess))
        except Exception as e: # Something went wrong with the binding
            port_guess += 1
            continue
        finally:
            s.close()
        
        return port_guess

REDIRECT_PORT = pick_free_port()
REDIRECT_URI = "http://%s:%u/" % (REDIRECT_HOST, REDIRECT_PORT)

def _make_code_post(code):
    client = Client(
        token_endpoint='https://accounts.google.com/o/oauth2/token',
        resource_endpoint='https://www.googleapis.com/oauth2/v1',
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    params = {"redirect_uri": REDIRECT_URI}
    client.request_token(code=code, **params)
    return client.access_token, client.refresh_token, client.expires_in

def make_refresh_post(refresh_token):
    client = Client(
        token_endpoint='https://accounts.google.com/o/oauth2/token',
        resource_endpoint='https://www.googleapis.com/oauth2/v1',
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    params = {"grant_type": "refresh_token"}
    client.request_token(refresh_token=refresh_token, **params)
    return client.access_token, client.expires_in

def get_storage():
    with open(REFRESH_FILE, 'rb') as fp:
        storage = pickle.load(fp)
    return storage['access_token'], storage['expires_at'], storage['refresh_token']

def update_storage(access_token, expires_in, refresh_token):
    cur_time = int(time.time())
    with open(REFRESH_FILE, 'wb') as fp:
        pickle.dump({
            'access_token': access_token,
            'expires_at': cur_time + expires_in,
            'refresh_token': refresh_token
        }, fp)

def authenticate(force=False):
    """
    Returns an oauth token that can be passed to the server for identification.
    """
    if not force:
        try:
            cur_time = int(time.time())
            access_token, expires_at, refresh_token = get_storage()
            if cur_time < expires_at - 10:
                return access_token
            access_token, expires_in = make_refresh_post(refresh_token)
            update_storage(access_token, expires_in, refresh_token)
            return access_token
        except IOError as _:
            print('Performing authentication')
        except Exception as _:
            print('Performing authentication')

    print("Please enter your CalNet ID.")
    calnet_id = input("CalNet ID: ")

    c = Client(auth_endpoint='https://accounts.google.com/o/oauth2/auth',
               client_id=CLIENT_ID)
    url = c.auth_uri(scope="profile email", access_type='offline',
                     name='ok-server', redirect_uri=REDIRECT_URI,
                     login_hint='%s@berkeley.edu' % (calnet_id))

    webbrowser.open_new(url)

    host_name = REDIRECT_HOST
    port_number = REDIRECT_PORT

    done = False
    access_token = None
    refresh_token = None
    expires_in = None

    class CodeHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            """Respond to the GET request made by the OAuth"""
            path = urlparse(self.path)
            nonlocal access_token, refresh_token, expires_in, done
            qs = parse_qs(path.query)
            code = qs['code'][0]
            access_token, refresh_token, expires_in = _make_code_post(code)

            done = True
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(SUCCESS_HTML, "utf-8"))

        def log_message(self, format, *args):
            return

    server_address = (host_name, port_number)
    httpd = http.server.HTTPServer(server_address, CodeHandler)
    httpd.handle_request()

    update_storage(access_token, expires_in, refresh_token)
    return access_token

if __name__ == "__main__":
    print(authenticate())
PK     8jDF��L��  �     client/utils/timer.py"""Timeout mechanism."""

from client import exceptions
import threading
import traceback

def timed(timeout, fn, args=(), kargs={}):
    """Evaluates expr in the given frame.

    PARAMETERS:
    fn      -- function; Python function to be evaluated
    args    -- tuple; positional arguments for fn
    kargs   -- dict; keyword arguments for fn
    timeout -- int; number of seconds before timer interrupt (defaults
               to TIMEOUT

    RETURN:
    Result of calling fn(*args, **kargs).

    RAISES:
    Timeout -- if thread takes longer than timemout to execute
    Error        -- if calling fn raises an error, raise it
    """
    submission = __ReturningThread(fn, args, kargs)
    submission.start()
    submission.join(timeout)
    if submission.is_alive():
        raise exceptions.Timeout(timeout)
    if submission.error is not None:
        raise submission.error
    return submission.result

class __ReturningThread(threading.Thread):
    """Creates a daemon Thread with a result variable."""
    def __init__(self, fn, args, kargs):
        super().__init__()
        self.daemon = True
        self.result = None
        self.error = None
        self.fn = fn
        self.args = args
        self.kargs = kargs

    def run(self):
        try:
            self.result = self.fn(*self.args, **self.kargs)
        except Exception as e:
            e._message = traceback.format_exc(limit=2)
            self.error = e

PK     8jDFk���  �     client/utils/network.py"""This module contains utilities for communicating with the ok server."""

from urllib import request, error
import json
import time
import datetime
import socket

TIMEOUT = 500
RETRY_LIMIT = 5

def send_to_server(access_token, messages, name, server, version, log,
        insecure=False):
    """Send messages to server, along with user authentication."""
    data = {
        'assignment': name,
        'messages': messages,
    }
    try:
        prefix = "http" if insecure else "https"
        address = prefix + '://' + server + '/api/v1/submission'
        serialized = json.dumps(data).encode(encoding='utf-8')
        # TODO(denero) Wrap in timeout (maybe use PR #51 timed execution).
        # TODO(denero) Send access token with the request
        address += "?access_token={0}&client_version={1}".format(
            access_token, version)

        log.info('Sending data to %s', address)
        req = request.Request(address)
        req.add_header("Content-Type", "application/json")
        response = request.urlopen(req, serialized, TIMEOUT)
        return json.loads(response.read().decode('utf-8'))
    except error.HTTPError as ex:
        log.warning('Error while sending to server: %s', str(ex))
        response = ex.read().decode('utf-8')
        response_json = json.loads(response)
        log.warning('Server error message: %s', response_json['message'])
        try:
            if ex.code == 403:
                if software_update(response_json['data']['download_link'], log):
                    raise SoftwareUpdated
            return {}
        except SoftwareUpdated as e:
            raise e
        #TODO(soumya) Figure out what exceptions can happen here specifically
        # I'll fix this after the ants project is over so we don't risk breaking
        # anything.
        except Exception as e:
            log.warning('Could not connect to %s', server)

def dump_to_server(access_token, msg_list, name, server, insecure, version, log, send_all=False):
    stop_time = datetime.datetime.now() + datetime.timedelta(milliseconds=TIMEOUT)
    initial_length = len(msg_list)
    retries = RETRY_LIMIT
    first_response = 1
    while msg_list:
        if not send_all and datetime.datetime.now() > stop_time:
            return
        message = msg_list[-1]
        try:
            response = send_to_server(access_token, message, name, server, version, log, insecure)

            if response:
                if type(first_response) == int and first_response > 0:
                    first_response -= 1
                else:
                    first_response = response
                msg_list.pop()
            elif retries > 0:
                retries -= 1
            else:
                print("Submission failed. Please check your network connection and try again")
                return

            if send_all:
                print("Submitting project... {0}% complete".format(100 - round(len(msg_list)*100/initial_length), 2))

        except SoftwareUpdated:
            print("ok was updated. We will now terminate this run of ok.")
            log.info('ok was updated. Abort now; messages will be sent '
                     'to server on next invocation')
            return
        except error.URLError as ex:
            log.warning('URLError: %s', str(ex))
        except socket.timeout as ex:
            log.warning("socket.timeout: %s", str(ex))

    # Assumption is that msg_list is ordered in chronogical order of creation. The last item in the list
    # is the stuff from this run, so the response from there contains the id that we can then display.
    return first_response

def server_timer():
    """Timeout for the server."""
    time.sleep(0.8)

#####################
# Software Updating #
#####################

class SoftwareUpdated(BaseException):
    pass

def software_update(download_link, log):
    """Check for the latest version of ok and update this file accordingly.

    RETURN:
    bool; True if the newest version of ok was written to the filesystem, False
    otherwise.
    """
    log.info('Retrieving latest version from %s', download_link)

    file_destination = 'ok'
    try:
        req = request.Request(download_link)
        log.info('Sending request to %s', download_link)
        response = request.urlopen(req)

        zip_binary = response.read()
        log.info('Writing new version to %s', file_destination)
        with open(file_destination, 'wb') as f:
            f.write(zip_binary)
            os.fsync(f)
        log.info('Successfully wrote to %s', file_destination)
        return True
    except error.HTTPError as e:
        log.warning('Error when downloading new version of ok: %s', str(e))
    except IOError as e:
        log.warning('Error writing to %s: %s', file_destination, str(e))
    return False
PK     8jDFa�� �  �     client/utils/output.py"""This module contains code related to controlling and writing to stdout."""

import os
import sys

class _OutputLogger(object):
    """Custom logger for capturing and suppressing standard output."""
    # TODO(albert): logger should fully implement output stream.

    def __init__(self):
        self._current_stream = self._stdout = sys.stdout
        self._devnull = open(os.devnull, 'w')
        self._logs = {}
        self._num_logs = 0

    def on(self):
        """Allows print statements to emit to standard output."""
        self._current_stream = self._stdout

    def off(self):
        """Prevents print statements from emitting to standard out."""
        self._current_stream = self._devnull

    def new_log(self):
        """Registers a new log so that calls to write will append to the log.

        RETURN:
        int; a unique ID to reference the log.
        """
        log_id = self._num_logs
        self._logs[log_id] = []
        self._num_logs += 1
        return log_id

    def get_log(self, log_id):
        assert log_id in self._logs
        return self._logs[log_id]

    def remove_log(self, log_id):
        assert log_id in self._logs, 'Log id {} not found'.format(log_id)
        del self._logs[log_id]

    def remove_all_logs(self):
        self._logs = {}

    def is_on(self):
        return self._current_stream == self._stdout

    def write(self, msg):
        """Writes msg to the current output stream (either standard
        out or dev/null). If a log has been registered, append msg
        to the log.

        PARAMTERS:
        msg -- str
        """
        self._current_stream.write(msg)
        for log in self._logs.values():
            log.append(msg)

    def flush(self):
        self._current_stream.flush()

    # TODO(albert): rewrite this to be cleaner.
    def __getattr__(self, attr):
        return getattr(self._current_stream, attr)

_logger = sys.stdout = _OutputLogger()

def on():
    _logger.on()

def off():
    _logger.off()

def get_log(log_id):
    return _logger.get_log(log_id)

def new_log():
    return _logger.new_log()

def remove_log(log_id):
    _logger.remove_log(log_id)

def remove_all_logs():
    _logger.remove_all_logs()
PK     8jDF�o��!  !  !   client/utils/sanction/__init__.py# vim: set ts=4 sw=)

from functools import wraps
from json import loads
from datetime import datetime, timedelta
from time import mktime
try:
    from urllib import urlencode
    from urllib2 import Request, urlopen
    from urlparse import urlsplit, urlunsplit, parse_qsl

    # monkeypatch httpmessage
    from httplib import HTTPMessage
    def get_charset(self):
        try:
            data = filter(lambda s: 'Content-Type' in s, self.headers)[0]
            if 'charset' in data:
                cs = data[data.index(';') + 1:-2].split('=')[1].lower()
                return cs
        except IndexError:
            pass

        return 'utf-8'
    HTTPMessage.get_content_charset = get_charset 
except ImportError: # pragma: no cover
    from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
    from urllib.request import Request, urlopen


class Client(object):
    """ OAuth 2.0 client object
    """

    def __init__(self, auth_endpoint=None, token_endpoint=None,
        resource_endpoint=None, client_id=None, client_secret=None,
        token_transport=None):
        """ Instantiates a `Client` to authorize and authenticate a user

        :param auth_endpoint: The authorization endpoint as issued by the
                              provider. This is where the user should be
                              redirect to provider authorization for your
                              application.
        :param token_endpoint: The endpoint against which a `code` will be
                               exchanged for an access token.
        :param resource_endpoint: The base url to use when accessing resources
                                  via `Client.request`.
        :param client_id: The client ID as issued by the provider.
        :param client_secret: The client secret as issued by the provider. This
                              must not be shared.
        """
        assert token_transport is None or hasattr(token_transport, '__call__')

        self.auth_endpoint = auth_endpoint
        self.token_endpoint = token_endpoint
        self.resource_endpoint = resource_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_transport = token_transport or transport_query
        self.token_expires = -1
        self.refresh_token = None

    def auth_uri(self, redirect_uri=None, scope=None, scope_delim=None, 
        state=None, **kwargs):

        """  Builds the auth URI for the authorization endpoint

        :param scope: (optional) The `scope` parameter to pass for
                      authorization. The format should match that expected by
                      the provider (i.e. Facebook expects comma-delimited,
                      while Google expects space-delimited)
        :param state: (optional) The `state` parameter to pass for
                      authorization. If the provider follows the OAuth 2.0
                      spec, this will be returned to your `redirect_uri` after
                      authorization. Generally used for CSRF protection.
        :param **kwargs: Any other querystring parameters to be passed to the
                         provider.
        """
        kwargs.update({
            'client_id': self.client_id,
            'response_type': 'code',
        })

        if scope is not None:
            kwargs['scope'] = scope

        if state is not None:
            kwargs['state'] = state

        if redirect_uri is not None:
            kwargs['redirect_uri'] = redirect_uri

        return '%s?%s' % (self.auth_endpoint, urlencode(kwargs))

    def request_token(self, parser=None, redirect_uri=None, **kwargs):
        """ Request an access token from the token endpoint.
        This is largely a helper method and expects the client code to
        understand what the server expects. Anything that's passed into
        ``**kwargs`` will be sent (``urlencode``d) to the endpoint. Client
        secret and client ID are automatically included, so are not required
        as kwargs. For example::

            # if requesting access token from auth flow:
            {
                'code': rval_from_auth,
            }

            # if refreshing access token:
            {
                'refresh_token': stored_refresh_token,
                'grant_type': 'refresh_token',
            }

        :param parser: Callback to deal with returned data. Not all providers
                       use JSON.
        """
        kwargs = kwargs and kwargs or {}

        parser = parser or _default_parser
        kwargs.update({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'grant_type' in kwargs and kwargs['grant_type'] or \
                'authorization_code'
        })
        if redirect_uri is not None:
            kwargs.update({'redirect_uri': redirect_uri})

        # TODO: maybe raise an exception here if status code isn't 200?
        msg = urlopen(self.token_endpoint, urlencode(kwargs).encode(
            'utf-8'))
        data = parser(msg.read().decode(msg.info().get_content_charset() or
            'utf-8'))

        for key in data:
            setattr(self, key, data[key])

        # expires_in is RFC-compliant. if anything else is used by the
        # provider, token_expires must be set manually
        if hasattr(self, 'expires_in'):
            try:
                # python3 dosn't support long
                seconds = long(self.expires_in)
            except:
                seconds = int(self.expires_in)
            self.token_expires = mktime((datetime.utcnow() + timedelta(
                seconds=seconds)).timetuple())

    def refresh(self):
        self.request_token(refresh_token=self.refresh_token,
            grant_type='refresh_token')

    def request(self, url, method=None, data=None, headers=None, parser=None): 
        """ Request user data from the resource endpoint
        :param url: The path to the resource and querystring if required
        :param method: HTTP method. Defaults to ``GET`` unless data is not None
                       in which case it defaults to ``POST``
        :param data: Data to be POSTed to the resource endpoint
        :param parser: Parser callback to deal with the returned data. Defaults
                       to ``json.loads`.`
        """
        assert self.access_token is not None
        parser = parser or loads 

        if not method:
            method = 'GET' if not data else 'POST'

        req = self.token_transport('{0}{1}'.format(self.resource_endpoint, 
            url), self.access_token, data=data, method=method, headers=headers)

        resp = urlopen(req)
        data = resp.read()
        try:
            return parser(data.decode(resp.info().get_content_charset() or
                'utf-8'))
            # try to decode it first using either the content charset, falling
            # back to utf-8

        except UnicodeDecodeError:
            # if we've gotten a decoder error, the calling code better know how
            # to deal with it. some providers (i.e. stackexchange) like to gzip
            # their responses, so this allows the client code to handle it
            # directly.
            return parser(data)


def transport_headers(url, access_token, data=None, method=None, headers=None):
    try:
        req = Request(url, data=data, method=method)
    except TypeError:
        req = Request(url, data=data)
        req.get_method = lambda: method

    add_headers = {'Authorization': 'Bearer {0}'.format(access_token)}
    if headers is not None:
        add_headers.update(headers)

    req.headers.update(add_headers)
    return req


def transport_query(url, access_token, data=None, method=None, headers=None):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query.update({
        'access_token': access_token
    })
    url = urlunsplit((parts.scheme, parts.netloc, parts.path,
        urlencode(query), parts.fragment))
    try:
        req = Request(url, data=data, method=method)
    except TypeError:
        req = Request(url, data=data)
        req.get_method = lambda: method

    if headers is not None:
        req.headers.update(headers)

    return req


def _default_parser(data):
    try:
        return loads(data)
    except ValueError:
        return dict(parse_qsl(data))
PK     8jDFk�q�         client/utils/sanction/client.pyfrom warnings import warn
warn('sanction.client.Client is deprecated, please use sanction.Client')
from sanction import Client
PK     8jDF��   �              ��    __main__.pyPK     \kDF�'��   �              ��  client/__init__.pyPK     \kDF0ZW$  $             ��  client/exceptions.pyPK     8jDF                       ��j  client/sources/__init__.pyPK     8jDF            !           ���  client/sources/common/__init__.pyPK     8jDFi�\��  �             ���  client/sources/common/models.pyPK     8jDF�-2��  �             ���  client/sources/common/core.pyPK     8jDF���,6%  6%  %           ���(  client/sources/common/doctest_case.pyPK     8jDF�;l�  �  "           ��2N  client/sources/common/importing.pyPK     8jDF��5t�  �  $           ��P  client/sources/common/interpreter.pyPK     8jDF�a�~�  �  "           ��WY  client/sources/ok_test/__init__.pyPK     8jDF�'P�                ��^  client/sources/ok_test/models.pyPK     8jDF�N9|	  |	  !           ��`y  client/sources/ok_test/doctest.pyPK     8jDF�mB�    !           ���  client/sources/ok_test/concept.pyPK     8jDF��p��	  �	  "           ��a�  client/sources/doctest/__init__.pyPK     8jDFߟ�
o  o              ����  client/sources/doctest/models.pyPK     8jDF���`  `             ��@�  client/protocols/unlock.pyPK     8jDF                       ��ؿ  client/protocols/__init__.pyPK     8jDF��`�               ���  client/protocols/scoring.pyPK     8jDF�h��V  V             ��h�  client/protocols/grading.pyPK     8jDF^Đ+  +             ����  client/protocols/lock.pyPK     8jDFZ/l�  �  !           ��X�  client/protocols/file_contents.pyPK     8jDFئ�V  V             ��!�  client/protocols/analytics.pyPK     8jDF            #           ����  client/protocols/common/__init__.pyPK     8jDF:��  �  !           ����  client/protocols/common/models.pyPK     \kDF                       ���  client/cli/__init__.pyPK     \kDFyH�h!  !             ��6�  client/cli/ok.pyPK     8jDF                       ��} client/cli/common/__init__.pyPK     8jDFe�L�"  "             ��� client/cli/common/assignment.pyPK     8jDFq~��  �             �� client/utils/format.pyPK     8jDF                       ��8* client/utils/__init__.pyPK     8jDFD�\O  O             ��n* client/utils/auth.pyPK     8jDF��L��  �             ���< client/utils/timer.pyPK     8jDFk���  �             ���B client/utils/network.pyPK     8jDFa�� �  �             ���U client/utils/output.pyPK     8jDF�o��!  !  !           ���^ client/utils/sanction/__init__.pyPK     8jDFk�q�                 ��� client/utils/sanction/client.pyPK    % % �
  ��   