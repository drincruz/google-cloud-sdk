# Copyright 2015 Google Inc. All Rights Reserved.

"""Helper functions for comparing semantic versions.

Basic rules of semver:

Format: major.minor.patch-prerelease+build

major, minor, patch, must all be present and integers with no leading zeros.
They are compared numerically by segment.

prerelease is an optional '.' separated series of identifiers where each is
either an integer with no leading zeros, or an alphanumeric string
(including '-'). Prereleases are compared by comparing each identifier in
order.  Integers are compared numerically, alphanumeric strings are compared
lexigraphically.  A prerelease version is lower precedence than it's associated
normal version.

The build number is optional and not included in the comparison.  It is '.'
separated series of alphanumeric identifiers.

Two SemVer objects are considered equal if they represent the exact same string
(including the build number and including case differences).  For comparison
operators, we follow the SemVer spec of precedence and ignore the build number
and case of alphanumeric strings.
"""

import re


# Only digits, with no leading zeros.
_DIGITS = r'(?:0|[1-9][0-9]*)'
# Digits, letters and dashes
_ALPHA_NUM = r'[-0-9A-Za-z]+'
# This is an alphanumeric string that must have at least once letter (or else it
# would be considered digits).
_STRICT_ALPHA_NUM = r'[-0-9A-Za-z]*[-A-Za-z]+[-0-9A-Za-z]*'

_PRE_RELEASE_IDENTIFIER = r'(?:{0}|{1})'.format(_DIGITS, _STRICT_ALPHA_NUM)
_PRE_RELEASE = r'(?:{0}(?:\.{0})*)'.format(_PRE_RELEASE_IDENTIFIER)
_BUILD = r'(?:{0}(?:\.{0})*)'.format(_ALPHA_NUM)

_SEMVER = (
    r'^(?P<major>{digits})\.(?P<minor>{digits})\.(?P<patch>{digits})'
    r'(?:\-(?P<prerelease>{release}))?(?:\+(?P<build>{build}))?$'
).format(digits=_DIGITS, release=_PRE_RELEASE, build=_BUILD)


class ParseError(Exception):
  """An exception for when a string failed to parse as a valid semver."""
  pass


class SemVer(object):
  """Object to hold a parsed semantic version string."""

  def __init__(self, version):
    """Creates a SemVer object from the given version string.

    Args:
      version: str, The version string to parse.

    Raises:
      ParseError: If the version could not be correctly parsed.

    Returns:
      SemVer, The parsed version.
    """
    (self.major, self.minor, self.patch, self.prerelease, self.build) = (
        SemVer._FromString(version))

  @classmethod
  def _FromString(cls, version):
    """Parse the given version string into its parts."""
    if version is None:
      raise ParseError('The value is not a valid SemVer string: [None]')

    try:
      match = re.match(_SEMVER, version)
    except (TypeError, re.error) as e:
      raise ParseError('Error parsing version string: [{0}].  {1}'
                       .format(version, e.message))

    if not match:
      raise ParseError(
          'The value is not a valid SemVer string: [{0}]'.format(version))

    parts = match.groupdict()
    return (
        int(parts['major']), int(parts['minor']), int(parts['patch']),
        parts['prerelease'], parts['build'])

  @classmethod
  def _ComparePrereleaseStrings(cls, s1, s2):
    """Compares the two given prerelease strings.

    Args:
      s1: str, The first prerelease string.
      s2: str, The second prerelease string.

    Returns:
      1 if s1 is greater than s2, -1 if s2 is greater than s1, and 0 if equal.
    """
    # No prerelease is greater than any version with a prerelease.
    if s1 is None and s2 is not None:
      return 1
    if s2 is None and s1 is not None:
      return -1

    # If both are the same (including None), they are equal
    if s1 == s2:
      return 0

    # Convert numeric segments into ints for numerical comparison.
    to_comparable = lambda part: int(part) if part.isdigit() else part.lower()
    # Split the version by dots so each part can be compared.
    get_parts = lambda s: [to_comparable(part) for part in s.split('.')]

    return cmp(get_parts(s1), get_parts(s2))

  def _Compare(self, other):
    """Compare this SemVer to other.

    Args:
      other: SemVer, the other version to compare this one to.

    Returns:
      1 if self > other, -1 if other > self, 0 if equal.
    """
    # Compare the required parts.
    result = cmp(
        (self.major, self.minor, self.patch),
        (other.major, other.minor, other.patch))
    # Only if required parts are equal, compare the prerelease strings.
    # Never include build number in comparison.
    result = result or SemVer._ComparePrereleaseStrings(
        self.prerelease, other.prerelease)
    return result

  def __eq__(self, other):
    return (
        (self.major, self.minor, self.patch, self.prerelease, self.build) ==
        (other.major, other.minor, other.patch, other.prerelease, other.build))

  def __ne__(self, other):
    return not self == other

  def __gt__(self, other):
    return self._Compare(other) > 0

  def __lt__(self, other):
    return self._Compare(other) < 0

  def __ge__(self, other):
    return not self < other

  def __le__(self, other):
    return not self > other
