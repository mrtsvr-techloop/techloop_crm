# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

# import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class UnitTestCRMProductTag(UnitTestCase):
	"""
	Unit tests for CRMProductTag.
	Use this class for testing individual functions and methods.
	"""

	pass


class IntegrationTestCRMProductTag(IntegrationTestCase):
	"""
	Integration tests for CRMProductTag.
	Use this class for testing document interactions.
	"""

	pass
