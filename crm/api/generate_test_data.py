"""Generate random test data for CRM: Contacts, Organizations, Leads, and Deals.

This script creates realistic test data with proper relationships between entities.
"""

import frappe
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


# Italian names and companies
FIRST_NAMES = [
    "Marco", "Giulia", "Alessandro", "Sofia", "Luca", "Emma", "Matteo", "Giorgia",
    "Andrea", "Chiara", "Francesco", "Valentina", "Simone", "Martina", "Davide", "Alessia",
    "Lorenzo", "Beatrice", "Riccardo", "Elisa", "Edoardo", "Francesca", "Tommaso", "Sara",
    "Gabriele", "Camilla", "Filippo", "Greta", "Nicolò", "Alice"
]

LAST_NAMES = [
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci",
    "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Costa", "Fontana",
    "Caruso", "Mancini", "Rizzo", "Moretti", "Barbieri", "Lombardi", "Giordano", "Rinaldi"
]

COMPANY_NAMES = [
    "Tecnologie Avanzate S.r.l.", "Soluzioni Digitali S.p.A.", "Innovazione Italia S.r.l.",
    "Sistemi Integrati S.p.A.", "Servizi Informatici S.r.l.", "Digital Solutions S.p.A.",
    "Software House Italia S.r.l.", "Cloud Services S.p.A.", "Network Solutions S.r.l.",
    "Tech Innovation S.p.A.", "Sviluppo Software S.r.l.", "IT Services S.p.A.",
    "Data Management S.r.l.", "Cyber Security S.p.A.", "Web Solutions S.r.l.",
    "Automazione Industriale S.p.A.", "Smart Systems S.r.l.", "Future Tech S.p.A.",
    "Mobile Apps S.r.l.", "AI Solutions S.p.A."
]

CITIES = [
    "Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze",
    "Bari", "Catania", "Venezia", "Verona", "Messina", "Padova", "Trieste"
]

STREETS = [
    "Via Roma", "Via Garibaldi", "Via Mazzini", "Via Verdi", "Via Dante", "Via Manzoni",
    "Corso Italia", "Corso Umberto", "Via Nazionale", "Via del Corso", "Via Cavour",
    "Via XX Settembre", "Via Veneto", "Via delle Piazzole", "Via delle Querce"
]

LEAD_STATUSES = ["New", "Contacted", "Negotiation", "Rescheduled", "Rejected"]
DEAL_STATUSES = ["New", "Preparation", "Rescheduled", "Completed"]
LOST_REASONS = [
    "Budget non disponibile",
    "Timing non adatto",
    "Scegliuto competitor",
    "Requisiti cambiati",
    "Non risponde",
    "Prezzo troppo alto"
]

EMPLOYEE_RANGES = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]


def get_random_products(count: int = None) -> List[Dict[str, Any]]:
    """Get random products from CRM Product."""
    products = frappe.get_all(
        "CRM Product",
        fields=["name", "product_code", "product_name", "standard_rate"],
        filters={"disabled": 0}
    )
    
    if not products:
        frappe.throw("No products found. Please create products first using 'Add Products' function.")
    
    if count:
        return random.sample(products, min(count, len(products)))
    return products


def generate_random_phone() -> str:
    """Generate a random Italian phone number."""
    return f"+39{random.randint(300000000, 399999999)}"


def generate_random_email(first_name: str, last_name: str, company: str = None) -> str:
    """Generate a random email address."""
    # Normalize: remove accents and special characters
    import unicodedata
    
    def normalize_text(text: str) -> str:
        # Remove accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # Remove spaces and special characters
        return text.lower().replace(" ", "").replace("'", "").replace("-", "").replace(".", "")
    
    clean_first = normalize_text(first_name)
    clean_last = normalize_text(last_name)
    
    domain = normalize_text(company) if company else "example"
    if domain and not domain.endswith("it"):
        domain = domain[:10]  # Limit domain length
    domains = ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com"]
    if domain and len(domain) > 3:
        domains.append(f"{domain}.it")
    
    return f"{clean_first}.{clean_last}@{random.choice(domains)}"


def create_random_contact() -> str:
    """Create a random Contact."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    email = generate_random_email(first_name, last_name)
    mobile_no = generate_random_phone()
    
    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": first_name,
        "last_name": last_name,
        "email_id": email,
        "mobile_no": mobile_no,
        "status": random.choice(["Passive", "Open", "Replied"])
    })
    
    contact.insert(ignore_permissions=True)
    return contact.name


def create_random_organization() -> str:
    """Create a random CRM Organization."""
    org_name = random.choice(COMPANY_NAMES)
    
    # Check if organization already exists
    existing = frappe.db.exists("CRM Organization", {"organization_name": org_name})
    if existing:
        return existing
    
    organization = frappe.get_doc({
        "doctype": "CRM Organization",
        "organization_name": org_name,
        "website": f"www.{org_name.lower().replace(' ', '').replace('.', '')}.it",
        "no_of_employees": random.choice(EMPLOYEE_RANGES),
        "annual_revenue": random.randint(50000, 5000000),
        "currency": "EUR"
    })
    
    organization.insert(ignore_permissions=True)
    return organization.name


def create_random_lead(contact_name: str = None, organization_name: str = None) -> str:
    """Create a random CRM Lead with products."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    email = generate_random_email(first_name, last_name)
    mobile_no = generate_random_phone()
    
    # Generate random dates
    order_date = datetime.now() - timedelta(days=random.randint(0, 30))
    delivery_date = order_date + timedelta(days=random.randint(1, 14))
    
    # Generate random city and region
    city = random.choice(CITIES)
    region = random.choice(["Lombardia", "Lazio", "Campania", "Sicilia", "Veneto", "Emilia-Romagna", "Piemonte", "Puglia", "Toscana", "Calabria"])
    zip_code = f"{random.randint(10000, 99999)}"
    
    # Create lead
    lead = frappe.get_doc({
        "doctype": "CRM Lead",
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "mobile_no": mobile_no,
        "status": random.choice(LEAD_STATUSES),
        "order_date": order_date.strftime("%Y-%m-%d"),
        "delivery_date": delivery_date.strftime("%Y-%m-%d"),
        "delivery_address": f"{random.choice(STREETS)}, {random.randint(1, 200)}, {city}",
        "delivery_region": region,
        "delivery_city": city,
        "delivery_zip": zip_code,
        "order_notes": random.choice([
            "Consegna urgente richiesta",
            "Consegna in orario lavorativo",
            "Contattare prima della consegna",
            "Consegna standard",
            ""
        ])
    })
    
    if organization_name:
        lead.organization = organization_name
    
    lead.insert(ignore_permissions=True)
    
    # Add random products
    products = get_random_products(count=random.randint(1, 4))
    total_amount = 0
    
    for product in products:
        qty = random.randint(1, 5)
        rate = product.get("standard_rate", random.randint(20, 100))
        amount = qty * rate
        
        product_child = frappe.get_doc({
            "doctype": "CRM Products",
            "parent": lead.name,
            "parenttype": "CRM Lead",
            "parentfield": "products",
            "product_code": product["product_code"],
            "product_name": product["product_name"],
            "qty": qty,
            "rate": rate,
            "amount": amount,
            "net_amount": amount
        })
        product_child.insert(ignore_permissions=True)
        total_amount += amount
    
    # Update totals
    lead.reload()
    lead.total = total_amount
    lead.net_total = total_amount
    lead.save(ignore_permissions=True)
    
    # Link contact if provided
    if contact_name:
        try:
            contact_doc = frappe.get_doc("Contact", contact_name)
            link_exists = any(
                link.link_doctype == "CRM Lead" and link.link_name == lead.name
                for link in contact_doc.links
            )
            if not link_exists:
                contact_doc.append("links", {
                    "link_doctype": "CRM Lead",
                    "link_name": lead.name,
                    "link_title": lead.lead_name
                })
                contact_doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error linking contact to lead: {str(e)}")
    
    return lead.name


def create_random_deal(lead_name: str = None, contact_name: str = None, organization_name: str = None) -> str:
    """Create a random CRM Deal with products."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    email = generate_random_email(first_name, last_name)
    mobile_no = generate_random_phone()
    
    # Generate random dates
    expected_closure_date = datetime.now() + timedelta(days=random.randint(7, 60))
    delivery_date = datetime.now() + timedelta(days=random.randint(1, 30))
    
    # Generate random city and region
    city = random.choice(CITIES)
    region = random.choice(["Lombardia", "Lazio", "Campania", "Sicilia", "Veneto", "Emilia-Romagna", "Piemonte", "Puglia", "Toscana", "Calabria"])
    zip_code = f"{random.randint(10000, 99999)}"
    
    deal_value = random.randint(500, 10000)
    probability = random.choice([10, 25, 50, 75, 90, 100])
    
    # Create deal
    deal = frappe.get_doc({
        "doctype": "CRM Deal",
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "mobile_no": mobile_no,
        "status": random.choice(DEAL_STATUSES),
        "deal_value": deal_value,
        "expected_deal_value": deal_value,
        "probability": probability,
        "expected_closure_date": expected_closure_date.strftime("%Y-%m-%d"),
        "delivery_date": delivery_date.strftime("%Y-%m-%d"),
        "delivery_address": f"{random.choice(STREETS)}, {random.randint(1, 200)}, {city}",
        "delivery_region": region,
        "delivery_city": city,
        "delivery_zip": zip_code,
        "order_notes": random.choice([
            "Deal in fase di negoziazione",
            "Cliente interessato",
            "Richiede preventivo dettagliato",
            "Follow-up necessario",
            ""
        ])
    })
    
    if organization_name:
        deal.organization = organization_name
    
    if lead_name:
        deal.lead = lead_name
    
    deal.insert(ignore_permissions=True)
    
    # Add random products
    products = get_random_products(count=random.randint(1, 4))
    total_amount = 0
    
    for product in products:
        qty = random.randint(1, 5)
        rate = product.get("standard_rate", random.randint(20, 100))
        amount = qty * rate
        
        product_child = frappe.get_doc({
            "doctype": "CRM Products",
            "parent": deal.name,
            "parenttype": "CRM Deal",
            "parentfield": "products",
            "product_code": product["product_code"],
            "product_name": product["product_name"],
            "qty": qty,
            "rate": rate,
            "amount": amount,
            "net_amount": amount
        })
        product_child.insert(ignore_permissions=True)
        total_amount += amount
    
    # Update totals
    deal.reload()
    deal.total = total_amount
    deal.net_total = total_amount
    deal.save(ignore_permissions=True)
    
    # Link contact if provided
    if contact_name:
        try:
            contact_doc = frappe.get_doc("Contact", contact_name)
            link_exists = any(
                link.link_doctype == "CRM Deal" and link.link_name == deal.name
                for link in contact_doc.links
            )
            if not link_exists:
                contact_doc.append("links", {
                    "link_doctype": "CRM Deal",
                    "link_name": deal.name,
                    "link_title": f"{deal.first_name} {deal.last_name}"
                })
                contact_doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error linking contact to deal: {str(e)}")
    
    return deal.name


@frappe.whitelist()
def generate_test_data(count: int = 20):
    """Generate random test data for CRM.
    
    Args:
        count: Number of orders to create (default: 20)
    
    Returns:
        Dict with summary of created data
    """
    frappe.only_for("System Manager")
    
    if not isinstance(count, int):
        count = int(count)
    
    created_contacts = []
    created_organizations = []
    created_leads = []
    created_deals = []
    
    try:
        for i in range(count):
            # Create contact (always)
            contact_name = create_random_contact()
            created_contacts.append(contact_name)
            
            # Create organization (sometimes)
            organization_name = None
            if random.choice([True, False]):  # 50% chance
                organization_name = create_random_organization()
                if organization_name not in created_organizations:
                    created_organizations.append(organization_name)
            
            # Create lead (always)
            lead_name = create_random_lead(
                contact_name=contact_name,
                organization_name=organization_name
            )
            created_leads.append(lead_name)
            
            # Create deal (always, sometimes linked to a random lead)
            lead_link = random.choice(created_leads) if created_leads and random.choice([True, False]) else None
            deal_name = create_random_deal(
                lead_name=lead_link,
                contact_name=contact_name,
                organization_name=organization_name
            )
            created_deals.append(deal_name)
            
            # Commit every 5 records
            if (i + 1) % 5 == 0:
                frappe.db.commit()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Created {count} test orders successfully",
            "summary": {
                "contacts": len(created_contacts),
                "organizations": len(created_organizations),
                "leads": len(created_leads),
                "deals": len(created_deals)
            },
            "created": {
                "contacts": created_contacts[:10],  # Show first 10
                "organizations": created_organizations[:10],
                "leads": created_leads[:10],
                "deals": created_deals[:10]
            }
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error generating test data: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "traceback": frappe.get_traceback()
        }

