# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	sl_entries = get_stock_ledger_entries(filters)

	data = []
	for sle in sl_entries:

		data.append([sle.date, sle.item_code,
		             sle.warehouse,
		             sle.actual_qty, sle.qty_after_transaction,
		             sle.process,
		             sle.voucher_type, sle.voucher_no,
		             sle.company])

	return columns, data


def get_columns():
	return [_("Date") + ":Datetime:95", _("Item") + ":Link/Item:130",
	        _("Warehouse") + ":Link/Warehouse:100",
	        _("Qty") + ":Float:50", _("Balance Qty") + ":Float:100",
	        _("Process") + "::100",
	        _("Voucher Type") + "::110", _("Voucher #") + ":Dynamic Link/Voucher Type:100",
	        _("Company") + ":Link/Company:100"]


def get_stock_ledger_entries(filters):
	if filters.get('conjugate_entries'):
		return frappe.db.sql("""
			select concat_ws(" ", posting_date, posting_time) as date,
				item_code, warehouse, actual_qty, qty_after_transaction, process,
				voucher_type, voucher_no, company
			from `tabStock Ledger Entry`
			where (voucher_type, voucher_no) in (
						select voucher_type, voucher_no
						from `tabStock Ledger Entry` where
						company = %(company)s and
						posting_date between %(from_date)s and %(to_date)s
						{sle_conditions}
					)
			order by posting_date desc, posting_time desc, name desc""" \
			                     .format(sle_conditions=get_sle_conditions(filters)),
		                     filters,
		                     as_dict=1
		)
	else:
		return frappe.db.sql("""select concat_ws(" ", posting_date, posting_time) as date,
				item_code, warehouse, actual_qty, qty_after_transaction, process,
				voucher_type, voucher_no, company
			from `tabStock Ledger Entry`
			where company = %(company)s and
				posting_date between %(from_date)s and %(to_date)s
				{sle_conditions}
				order by posting_date desc, posting_time desc, name desc""" \
			                     .format(sle_conditions=get_sle_conditions(filters)), filters, as_dict=1)


def get_item_details(filters):
	item_details = {}
	for item in frappe.db.sql("""SELECT name, item_name, description, item_group,
			brand, stock_uom FROM `tabItem` {item_conditions}""" \
			                          .format(item_conditions=get_item_conditions(filters)), filters, as_dict=1):
		item_details.setdefault(item.name, item)

	return item_details


def get_item_conditions(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("name=%(item_code)s")
	if filters.get("brand"):
		conditions.append("brand=%(brand)s")

	return "where {}".format(" and ".join(conditions)) if conditions else ""


def get_sle_conditions(filters):
	conditions = []
	item_conditions = get_item_conditions(filters)
	if item_conditions:
		conditions.append("""item_code in (select name from tabItem
			{item_conditions})""".format(item_conditions=item_conditions))
	if filters.get("warehouse"):
		conditions.append("warehouse=%(warehouse)s")
	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""
