from __future__ import annotations
import re
import logging
from typing import Dict, List, Optional
from modules.screener.schemas import StockMeta

logger = logging.getLogger(__name__)

class UniverseManager:
    
    BANKING_FINANCIAL: Dict[str, StockMeta] = {
        "HDFCBANK.NS": StockMeta(name="HDFC Bank Limited", symbol="HDFCBANK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Consistent loan growth and post-merger synergy realization.", country="IN"),
        "ICICIBANK.NS": StockMeta(name="ICICI Bank Limited", symbol="ICICIBANK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Strong retail franchise and digital banking leadership.", country="IN"),
        "SBIN.NS": StockMeta(name="State Bank of India", symbol="SBIN", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Improving asset quality and strong corporate credit cycle.", country="IN"),
        "KOTAKBANK.NS": StockMeta(name="Kotak Mahindra Bank Limited", symbol="KOTAKBANK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Focus on unsecured retail lending and succession transition.", country="IN"),
        "BAJFINANCE.NS": StockMeta(name="Bajaj Finance Limited", symbol="BAJFINANCE", exchange="NSE", sector="banking_financial", industry="Consumer Finance", cap_tier="large_cap", fno_eligible=True, catalyst="AUM growth in consumer durables and omnichannel expansion.", country="IN"),
        "AXISBANK.NS": StockMeta(name="Axis Bank Limited", symbol="AXISBANK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Citi acquisition synergies and digital transformation.", country="IN"),
        "INDUSINDBK.NS": StockMeta(name="IndusInd Bank Limited", symbol="INDUSINDBK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Vehicle finance recovery and microfinance stability.", country="IN"),
        "FEDERALBNK.NS": StockMeta(name="The Federal Bank Limited", symbol="FEDERALBNK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="mid_cap", fno_eligible=True, catalyst="Strong deposit franchise and fintech partnerships.", country="IN"),
        "BANDHANBNK.NS": StockMeta(name="Bandhan Bank Limited", symbol="BANDHANBNK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="mid_cap", fno_eligible=True, catalyst="Geographical diversification and housing finance growth.", country="IN"),
        "IDFCFIRSTB.NS": StockMeta(name="IDFC FIRST Bank Limited", symbol="IDFCFIRSTB", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="mid_cap", fno_eligible=True, catalyst="Retailization of deposit base and loan book.", country="IN"),
        "PNB.NS": StockMeta(name="Punjab National Bank", symbol="PNB", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Asset quality turnaround and core earnings improvement.", country="IN"),
        "BANKBARODA.NS": StockMeta(name="Bank of Baroda", symbol="BANKBARODA", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Robust margin profile and international business growth.", country="IN"),
        "CANBK.NS": StockMeta(name="Canara Bank", symbol="CANBK", exchange="NSE", sector="banking_financial", industry="Banks", cap_tier="large_cap", fno_eligible=True, catalyst="Strong provision coverage and recovery in loan growth.", country="IN"),
        "BAJAJFINSV.NS": StockMeta(name="Bajaj Finserv Limited", symbol="BAJAJFINSV", exchange="NSE", sector="banking_financial", industry="Holding Companies", cap_tier="large_cap", fno_eligible=True, catalyst="Value unlocking in insurance and AMC businesses.", country="IN"),
        "SBILIFE.NS": StockMeta(name="SBI Life Insurance Company", symbol="SBILIFE", exchange="NSE", sector="banking_financial", industry="Insurance", cap_tier="large_cap", fno_eligible=True, catalyst="Bancassurance dominance and strong VNB margins.", country="IN"),
        "HDFCLIFE.NS": StockMeta(name="HDFC Life Insurance Company", symbol="HDFCLIFE", exchange="NSE", sector="banking_financial", industry="Insurance", cap_tier="large_cap", fno_eligible=True, catalyst="Product innovation and agency channel expansion.", country="IN"),
        "ICICIPRULI.NS": StockMeta(name="ICICI Prudential Life Insurance", symbol="ICICIPRULI", exchange="NSE", sector="banking_financial", industry="Insurance", cap_tier="large_cap", fno_eligible=True, catalyst="Balanced product mix and non-par savings growth.", country="IN"),
        "CHOLAFIN.NS": StockMeta(name="Cholamandalam Investment", symbol="CHOLAFIN", exchange="NSE", sector="banking_financial", industry="Consumer Finance", cap_tier="large_cap", fno_eligible=True, catalyst="Diversification into SME and new auto segment growth.", country="IN"),
        "MANAPPURAM.NS": StockMeta(name="Manappuram Finance Limited", symbol="MANAPPURAM", exchange="NSE", sector="banking_financial", industry="Consumer Finance", cap_tier="small_cap", fno_eligible=True, catalyst="Gold loan traction and microfinance recovery.", country="IN"),
        "MUTHOOTFIN.NS": StockMeta(name="Muthoot Finance Limited", symbol="MUTHOOTFIN", exchange="NSE", sector="banking_financial", industry="Consumer Finance", cap_tier="large_cap", fno_eligible=True, catalyst="Dominant gold loan franchise with high yields.", country="IN"),
        "LICHSGFIN.NS": StockMeta(name="LIC Housing Finance", symbol="LICHSGFIN", exchange="NSE", sector="banking_financial", industry="Housing Finance", cap_tier="mid_cap", fno_eligible=True, catalyst="Stable cost of funds and robust housing demand.", country="IN"),
        "IIFL.NS": StockMeta(name="IIFL Finance Limited", symbol="IIFL", exchange="NSE", sector="banking_financial", industry="Consumer Finance", cap_tier="small_cap", fno_eligible=False, catalyst="Diversified NBFC model with focus on core loans.", country="IN"),
        "ANGELONE.NS": StockMeta(name="Angel One Limited", symbol="ANGELONE", exchange="NSE", sector="banking_financial", industry="Capital Markets", cap_tier="small_cap", fno_eligible=True, catalyst="Market share gains in retail broking.", country="IN"),
        "CDSL.NS": StockMeta(name="Central Depository Services", symbol="CDSL", exchange="NSE", sector="banking_financial", industry="Capital Markets", cap_tier="small_cap", fno_eligible=False, catalyst="Beneficiary of growing retail participation in equities.", country="IN"),
        "KFINTECH.NS": StockMeta(name="KFin Technologies Limited", symbol="KFINTECH", exchange="NSE", sector="banking_financial", industry="Capital Markets", cap_tier="small_cap", fno_eligible=False, catalyst="International expansion and mutual fund RTA dominance.", country="IN"),
    }

    IT_SOFTWARE: Dict[str, StockMeta] = {
        "TCS.NS": StockMeta(name="Tata Consultancy Services", symbol="TCS", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="large_cap", fno_eligible=True, catalyst="Cost optimization deals and generative AI adoption.", country="IN"),
        "INFY.NS": StockMeta(name="Infosys Limited", symbol="INFY", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="large_cap", fno_eligible=True, catalyst="Strong large deal momentum and margin resilience.", country="IN"),
        "WIPRO.NS": StockMeta(name="Wipro Limited", symbol="WIPRO", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="large_cap", fno_eligible=True, catalyst="Turnaround strategy and consulting business stabilization.", country="IN"),
        "HCLTECH.NS": StockMeta(name="HCL Technologies Limited", symbol="HCLTECH", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="large_cap", fno_eligible=True, catalyst="Software products segment and ER&D leadership.", country="IN"),
        "TECHM.NS": StockMeta(name="Tech Mahindra Limited", symbol="TECHM", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="large_cap", fno_eligible=True, catalyst="Telecom 5G rollout cycle and organizational restructuring.", country="IN"),
        "LTIM.NS": StockMeta(name="LTIMindtree Limited", symbol="LTIM", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="large_cap", fno_eligible=True, catalyst="Merger synergies and cross-selling across client base.", country="IN"),
        "COFORGE.NS": StockMeta(name="Coforge Limited", symbol="COFORGE", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="mid_cap", fno_eligible=True, catalyst="Travel and BFS vertical recovery and strong order book.", country="IN"),
        "MPHASIS.NS": StockMeta(name="Mphasis Limited", symbol="MPHASIS", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="mid_cap", fno_eligible=True, catalyst="Direct core business growth and mortgage segment revival.", country="IN"),
        "PERSISTENT.NS": StockMeta(name="Persistent Systems", symbol="PERSISTENT", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="mid_cap", fno_eligible=True, catalyst="Product engineering prowess and healthcare IT focus.", country="IN"),
        "CYIENT.NS": StockMeta(name="Cyient Limited", symbol="CYIENT", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="small_cap", fno_eligible=False, catalyst="Aerospace recovery and DLM business hiving off.", country="IN"),
        "SONATSOFTW.NS": StockMeta(name="Sonata Software", symbol="SONATSOFTW", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="small_cap", fno_eligible=False, catalyst="Microsoft Dynamics partnership and international growth.", country="IN"),
        "ZENSAR.NS": StockMeta(name="Zensar Technologies", symbol="ZENSAR", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="small_cap", fno_eligible=False, catalyst="Margin expansion under new leadership.", country="IN"),
        "BIRLASOFT.NS": StockMeta(name="Birlasoft Limited", symbol="BIRLASOFT", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="small_cap", fno_eligible=True, catalyst="ERP consulting strength and focused vertical strategy.", country="IN"),
        "MASTEK.NS": StockMeta(name="Mastek Limited", symbol="MASTEK", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="small_cap", fno_eligible=False, catalyst="UK government digital transformation projects.", country="IN"),
        "NEWGEN.NS": StockMeta(name="Newgen Software Tech", symbol="NEWGEN", exchange="NSE", sector="it_software", industry="Software", cap_tier="small_cap", fno_eligible=False, catalyst="Subscription-led growth in banking SaaS products.", country="IN"),
        "HAPPSTMNDS.NS": StockMeta(name="Happiest Minds Tech", symbol="HAPPSTMNDS", exchange="NSE", sector="it_software", industry="IT Services", cap_tier="small_cap", fno_eligible=False, catalyst="Pure-play digital focus and agile delivery.", country="IN"),
        "ROUTE.NS": StockMeta(name="Route Mobile Limited", symbol="ROUTE", exchange="NSE", sector="it_software", industry="Software", cap_tier="small_cap", fno_eligible=False, catalyst="CPaaS market expansion and Proximus integration.", country="IN"),
        "TATAELXSI.NS": StockMeta(name="Tata Elxsi Limited", symbol="TATAELXSI", exchange="NSE", sector="it_software", industry="Engineering R&D", cap_tier="mid_cap", fno_eligible=True, catalyst="Automotive EV/connected car ER&D demand.", country="IN"),
        "KPITTECH.NS": StockMeta(name="KPIT Technologies", symbol="KPITTECH", exchange="NSE", sector="it_software", industry="Engineering R&D", cap_tier="mid_cap", fno_eligible=False, catalyst="Software-defined vehicles and large auto OEM deals.", country="IN"),
        "DATAPATTNS.NS": StockMeta(name="Data Patterns (India)", symbol="DATAPATTNS", exchange="NSE", sector="it_software", industry="Engineering R&D", cap_tier="small_cap", fno_eligible=False, catalyst="Indigenization in defense electronics.", country="IN"),
    }

    PHARMA_HEALTHCARE: Dict[str, StockMeta] = {
        "SUNPHARMA.NS": StockMeta(name="Sun Pharmaceutical", symbol="SUNPHARMA", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=True, catalyst="Specialty portfolio ramp-up in the US market.", country="IN"),
        "DRREDDY.NS": StockMeta(name="Dr. Reddy's Labs", symbol="DRREDDY", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=True, catalyst="Complex generics pipeline and biosimilars.", country="IN"),
        "CIPLA.NS": StockMeta(name="Cipla Limited", symbol="CIPLA", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=True, catalyst="Respiratory franchise strength and US generics.", country="IN"),
        "DIVISLAB.NS": StockMeta(name="Divi's Laboratories", symbol="DIVISLAB", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=True, catalyst="Custom synthesis opportunities and generic API growth.", country="IN"),
        "APOLLOHOSP.NS": StockMeta(name="Apollo Hospitals", symbol="APOLLOHOSP", exchange="NSE", sector="pharma_healthcare", industry="Healthcare Facilities", cap_tier="large_cap", fno_eligible=True, catalyst="HealthCo digital platform scaling and core hospital occupancy.", country="IN"),
        "MAXHEALTH.NS": StockMeta(name="Max Healthcare", symbol="MAXHEALTH", exchange="NSE", sector="pharma_healthcare", industry="Healthcare Facilities", cap_tier="large_cap", fno_eligible=True, catalyst="Capacity expansion in high-ARPOB NCR region.", country="IN"),
        "BIOCON.NS": StockMeta(name="Biocon Limited", symbol="BIOCON", exchange="NSE", sector="pharma_healthcare", industry="Biotechnology", cap_tier="mid_cap", fno_eligible=True, catalyst="Viatris biosimilar integration and new approvals.", country="IN"),
        "LUPIN.NS": StockMeta(name="Lupin Limited", symbol="LUPIN", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=True, catalyst="Margin recovery and key respiratory product launches.", country="IN"),
        "AUROPHARMA.NS": StockMeta(name="Aurobindo Pharma", symbol="AUROPHARMA", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=True, catalyst="Injectables portfolio growth and PLI benefits.", country="IN"),
        "TORNTPHARM.NS": StockMeta(name="Torrent Pharmaceuticals", symbol="TORNTPHARM", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=True, catalyst="Curatio acquisition synergies and chronic therapy focus.", country="IN"),
        "ALKEM.NS": StockMeta(name="Alkem Laboratories", symbol="ALKEM", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="mid_cap", fno_eligible=True, catalyst="Domestic acute therapy leadership and trade generics.", country="IN"),
        "IPCALAB.NS": StockMeta(name="Ipca Laboratories", symbol="IPCALAB", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="mid_cap", fno_eligible=True, catalyst="Unichem acquisition turnaround and API revival.", country="IN"),
        "GLENMARK.NS": StockMeta(name="Glenmark Pharma", symbol="GLENMARK", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="mid_cap", fno_eligible=True, catalyst="Ryallbris rollout and debt reduction post-GLS sale.", country="IN"),
        "LALPATHLAB.NS": StockMeta(name="Dr. Lal PathLabs", symbol="LALPATHLAB", exchange="NSE", sector="pharma_healthcare", industry="Healthcare Services", cap_tier="mid_cap", fno_eligible=True, catalyst="Volume recovery and tier-3 geographic expansion.", country="IN"),
        "METROPOLIS.NS": StockMeta(name="Metropolis Healthcare", symbol="METROPOLIS", exchange="NSE", sector="pharma_healthcare", industry="Healthcare Services", cap_tier="mid_cap", fno_eligible=True, catalyst="B2C shift and specialized testing growth.", country="IN"),
        "PPLPHARMA.NS": StockMeta(name="Piramal Pharma", symbol="PPLPHARMA", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="small_cap", fno_eligible=False, catalyst="CDMO margin expansion and complex hospital generics.", country="IN"),
        "NEULANDLAB.NS": StockMeta(name="Neuland Laboratories", symbol="NEULANDLAB", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="small_cap", fno_eligible=False, catalyst="Shift towards high-margin CMS business.", country="IN"),
        "MARKSANS.NS": StockMeta(name="Marksans Pharma", symbol="MARKSANS", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="small_cap", fno_eligible=False, catalyst="OTC market penetration in US and UK.", country="IN"),
        "NATCOPHARM.NS": StockMeta(name="Natco Pharma", symbol="NATCOPHARM", exchange="NSE", sector="pharma_healthcare", industry="Pharmaceuticals", cap_tier="small_cap", fno_eligible=False, catalyst="Revlimid generic cash flows and agrochemical scale-up.", country="IN"),
        "SYNGENE.NS": StockMeta(name="Syngene International", symbol="SYNGENE", exchange="NSE", sector="pharma_healthcare", industry="Biotechnology", cap_tier="mid_cap", fno_eligible=True, catalyst="CRO to CDMO transition and biologic manufacturing.", country="IN"),
    }

    AUTO_ANCILLARIES: Dict[str, StockMeta] = {
        "MARUTI.NS": StockMeta(name="Maruti Suzuki", symbol="MARUTI", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="SUV market share gains and hybrid powertrain push.", country="IN"),
        "TATAMOTORS.NS": StockMeta(name="Tata Motors", symbol="TATAMOTORS", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="JLR deleveraging and domestic EV leadership.", country="IN"),
        "M&M.NS": StockMeta(name="Mahindra & Mahindra", symbol="M&M", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="Robust SUV backlog and tractor cycle recovery.", country="IN"),
        "EICHERMOT.NS": StockMeta(name="Eicher Motors", symbol="EICHERMOT", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="Premiumization in motorcycles and new model launches.", country="IN"),
        "HEROMOTOCO.NS": StockMeta(name="Hero MotoCorp", symbol="HEROMOTOCO", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="Rural demand revival and premium segment push.", country="IN"),
        "ASHOKLEY.NS": StockMeta(name="Ashok Leyland", symbol="ASHOKLEY", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="CV cycle upturn and defense mobility orders.", country="IN"),
        "BAJAJ-AUTO.NS": StockMeta(name="Bajaj Auto", symbol="BAJAJ-AUTO", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="Export recovery and Triumph partnership traction.", country="IN"),
        "TVSMOTOR.NS": StockMeta(name="TVS Motor Company", symbol="TVSMOTOR", exchange="NSE", sector="auto_ancillaries", industry="Automobiles", cap_tier="large_cap", fno_eligible=True, catalyst="EV scooter expansion and export market stability.", country="IN"),
        "BALKRISIND.NS": StockMeta(name="Balkrishna Industries", symbol="BALKRISIND", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="mid_cap", fno_eligible=True, catalyst="Global OTR tire demand and easing freight costs.", country="IN"),
        "MOTHERSON.NS": StockMeta(name="Samvardhana Motherson", symbol="MOTHERSON", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="large_cap", fno_eligible=True, catalyst="Non-auto diversification and global EV parts growth.", country="IN"),
        "BHARATFORG.NS": StockMeta(name="Bharat Forge", symbol="BHARATFORG", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="large_cap", fno_eligible=True, catalyst="Defense export orders and aerospace components.", country="IN"),
        "BOSCHLTD.NS": StockMeta(name="Bosch Limited", symbol="BOSCHLTD", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="large_cap", fno_eligible=True, catalyst="Transition to advanced emission norms and localized content.", country="IN"),
        "EXIDEIND.NS": StockMeta(name="Exide Industries", symbol="EXIDEIND", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="mid_cap", fno_eligible=True, catalyst="Lithium-ion cell manufacturing plant progress.", country="IN"),
        "AMARARAJA.NS": StockMeta(name="Amara Raja Energy", symbol="AMARARAJA", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="mid_cap", fno_eligible=True, catalyst="Lead-acid market share and new energy venture.", country="IN"),
        "ENDURANCE.NS": StockMeta(name="Endurance Technologies", symbol="ENDURANCE", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="mid_cap", fno_eligible=False, catalyst="ABS/Alloy wheel penetration in 2-wheelers.", country="IN"),
        "SUNDRMFAST.NS": StockMeta(name="Sundram Fasteners", symbol="SUNDRMFAST", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="mid_cap", fno_eligible=False, catalyst="EV component additions and export stability.", country="IN"),
        "MRF.NS": StockMeta(name="MRF Limited", symbol="MRF", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="large_cap", fno_eligible=True, catalyst="Raw material cost tailwinds and premium tire mix.", country="IN"),
        "CUMMINSIND.NS": StockMeta(name="Cummins India", symbol="CUMMINSIND", exchange="NSE", sector="auto_ancillaries", industry="Auto Components", cap_tier="large_cap", fno_eligible=True, catalyst="CPCB-IV+ emission norm transition and export strength.", country="IN"),
    }

    GEMS_JEWELLERY: Dict[str, StockMeta] = {
        "TITAN.NS": StockMeta(name="Titan Company", symbol="TITAN", exchange="NSE", sector="gems_jewellery", industry="Luxury Goods", cap_tier="large_cap", fno_eligible=True, catalyst="Market share gains from unorganized sector and store expansion.", country="IN"),
        "KALYANKJIL.NS": StockMeta(name="Kalyan Jewellers", symbol="KALYANKJIL", exchange="NSE", sector="gems_jewellery", industry="Luxury Goods", cap_tier="mid_cap", fno_eligible=False, catalyst="Franchise model expansion and Middle East growth.", country="IN"),
        "SENCO.NS": StockMeta(name="Senco Gold", symbol="SENCO", exchange="NSE", sector="gems_jewellery", industry="Luxury Goods", cap_tier="small_cap", fno_eligible=False, catalyst="Studded jewelry ratio improvement and North India expansion.", country="IN"),
        "VAIBHAVGBL.NS": StockMeta(name="Vaibhav Global", symbol="VAIBHAVGBL", exchange="NSE", sector="gems_jewellery", industry="Luxury Goods", cap_tier="small_cap", fno_eligible=False, catalyst="Omnichannel D2C growth in US/UK markets.", country="IN"),
        "THANGAMAYL.NS": StockMeta(name="Thangamayil Jewellery", symbol="THANGAMAYL", exchange="NSE", sector="gems_jewellery", industry="Luxury Goods", cap_tier="small_cap", fno_eligible=False, catalyst="Strong regional brand equity in Tamil Nadu.", country="IN"),
        "PCJEWELLER.NS": StockMeta(name="PC Jeweller", symbol="PCJEWELLER", exchange="NSE", sector="gems_jewellery", industry="Luxury Goods", cap_tier="small_cap", fno_eligible=False, catalyst="Debt restructuring and operational turnaround.", country="IN"),
    }

    TEXTILES_APPAREL: Dict[str, StockMeta] = {
        "PAGEIND.NS": StockMeta(name="Page Industries", symbol="PAGEIND", exchange="NSE", sector="textiles_apparel", industry="Apparel", cap_tier="large_cap", fno_eligible=True, catalyst="Athleisure demand stabilization and distribution expansion.", country="IN"),
        "KPRMILL.NS": StockMeta(name="K.P.R. Mill", symbol="KPRMILL", exchange="NSE", sector="textiles_apparel", industry="Textiles", cap_tier="mid_cap", fno_eligible=False, catalyst="Garment capacity additions and integrated model benefits.", country="IN"),
        "RAYMOND.NS": StockMeta(name="Raymond Limited", symbol="RAYMOND", exchange="NSE", sector="textiles_apparel", industry="Apparel", cap_tier="mid_cap", fno_eligible=False, catalyst="Demerger of lifestyle business and real estate monetization.", country="IN"),
        "TRIDENT.NS": StockMeta(name="Trident Limited", symbol="TRIDENT", exchange="NSE", sector="textiles_apparel", industry="Textiles", cap_tier="small_cap", fno_eligible=False, catalyst="Home textile export recovery and paper margin improvement.", country="IN"),
        "WELSPUNLIV.NS": StockMeta(name="Welspun Living", symbol="WELSPUNLIV", exchange="NSE", sector="textiles_apparel", industry="Textiles", cap_tier="small_cap", fno_eligible=False, catalyst="Advanced textiles growth and US market restocking.", country="IN"),
        "GOKEX.NS": StockMeta(name="Gokaldas Exports", symbol="GOKEX", exchange="NSE", sector="textiles_apparel", industry="Apparel", cap_tier="small_cap", fno_eligible=False, catalyst="China+1 strategy benefits and Atraco acquisition synergies.", country="IN"),
    }

    DEFENCE_AEROSPACE: Dict[str, StockMeta] = {
        "HAL.NS": StockMeta(name="Hindustan Aeronautics", symbol="HAL", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="large_cap", fno_eligible=True, catalyst="Tejas MK-1A deliveries and engine manufacturing deals.", country="IN"),
        "BEL.NS": StockMeta(name="Bharat Electronics", symbol="BEL", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="large_cap", fno_eligible=True, catalyst="Strong non-defense diversification and radar systems orderbook.", country="IN"),
        "BDL.NS": StockMeta(name="Bharat Dynamics", symbol="BDL", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="mid_cap", fno_eligible=False, catalyst="Missile systems export potential and indigenization.", country="IN"),
        "DATAPATTNS.NS": StockMeta(name="Data Patterns", symbol="DATAPATTNS", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="small_cap", fno_eligible=False, catalyst="Radar and electronic warfare system developments.", country="IN"),
        "SOLARINDS.NS": StockMeta(name="Solar Industries", symbol="SOLARINDS", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="large_cap", fno_eligible=False, catalyst="Defense ammunition scale-up and mining explosives growth.", country="IN"),
        "BEML.NS": StockMeta(name="BEML Limited", symbol="BEML", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="small_cap", fno_eligible=False, catalyst="Metro rail coaches and defense mobility vehicles.", country="IN"),
        "GRSE.NS": StockMeta(name="Garden Reach Shipbuilders", symbol="GRSE", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="small_cap", fno_eligible=False, catalyst="Next-gen corvette orders and export shipbuilding.", country="IN"),
        "COCHINSHIP.NS": StockMeta(name="Cochin Shipyard", symbol="COCHINSHIP", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="mid_cap", fno_eligible=False, catalyst="Ship repair facility expansion and aircraft carrier expertise.", country="IN"),
        "MAZAGON.NS": StockMeta(name="Mazagon Dock", symbol="MAZAGON", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="mid_cap", fno_eligible=False, catalyst="Submarine fleet expansion and stealth frigate deliveries.", country="IN"),
        "PARAS.NS": StockMeta(name="Paras Defence", symbol="PARAS", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="small_cap", fno_eligible=False, catalyst="Space optics and drone components capabilities.", country="IN"),
        "AABORANGE.NS": StockMeta(name="Apollo Micro Systems", symbol="AABORANGE", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="small_cap", fno_eligible=False, catalyst="Electronics manufacturing scaling.", country="IN"),
        "ZENTEC.NS": StockMeta(name="Zen Technologies", symbol="ZENTEC", exchange="NSE", sector="defence_aerospace", industry="Aerospace & Defense", cap_tier="small_cap", fno_eligible=False, catalyst="Anti-drone systems and defense training simulators.", country="IN"),
    }

    POWER_ENERGY: Dict[str, StockMeta] = {
        "NTPC.NS": StockMeta(name="NTPC Limited", symbol="NTPC", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="large_cap", fno_eligible=True, catalyst="Renewable energy IPO value unlocking and thermal capacity additions.", country="IN"),
        "POWERGRID.NS": StockMeta(name="Power Grid Corp", symbol="POWERGRID", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="large_cap", fno_eligible=True, catalyst="Transmission capex cycle for renewable energy integration.", country="IN"),
        "TATAPOWER.NS": StockMeta(name="Tata Power", symbol="TATAPOWER", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="large_cap", fno_eligible=True, catalyst="Solar EPC order book and EV charging network expansion.", country="IN"),
        "ADANIGREEN.NS": StockMeta(name="Adani Green Energy", symbol="ADANIGREEN", exchange="NSE", sector="power_energy", industry="Renewable Energy", cap_tier="large_cap", fno_eligible=False, catalyst="Aggressive capacity additions towards 45GW goal.", country="IN"),
        "NHPC.NS": StockMeta(name="NHPC Limited", symbol="NHPC", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="large_cap", fno_eligible=False, catalyst="Subansiri Lower project commissioning and pumped storage.", country="IN"),
        "SUZLON.NS": StockMeta(name="Suzlon Energy", symbol="SUZLON", exchange="NSE", sector="power_energy", industry="Renewable Energy", cap_tier="large_cap", fno_eligible=False, catalyst="Debt-free balance sheet and strong wind turbine orderbook.", country="IN"),
        "INOXWIND.NS": StockMeta(name="Inox Wind", symbol="INOXWIND", exchange="NSE", sector="power_energy", industry="Renewable Energy", cap_tier="small_cap", fno_eligible=False, catalyst="3.3MW WTG transition and healthy order execution.", country="IN"),
        "SJVN.NS": StockMeta(name="SJVN Limited", symbol="SJVN", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="mid_cap", fno_eligible=False, catalyst="Hydro power commissioning and thermal/solar additions.", country="IN"),
        "CESC.NS": StockMeta(name="CESC Limited", symbol="CESC", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="mid_cap", fno_eligible=False, catalyst="Distribution franchisee growth and renewable transition.", country="IN"),
        "TORNTPOWER.NS": StockMeta(name="Torrent Power", symbol="TORNTPOWER", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="mid_cap", fno_eligible=True, catalyst="Gas-based power revival and pump storage projects.", country="IN"),
        "JSW.NS": StockMeta(name="JSW Energy", symbol="JSW", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="large_cap", fno_eligible=False, catalyst="Mytrah integration and rapid renewable capacity ramp-up.", country="IN"),
        "ADANIENSOL.NS": StockMeta(name="Adani Energy Solutions", symbol="ADANIENSOL", exchange="NSE", sector="power_energy", industry="Utilities", cap_tier="large_cap", fno_eligible=False, catalyst="Smart metering contracts and transmission assets.", country="IN"),
        "IREDA.NS": StockMeta(name="Indian Renewable Energy", symbol="IREDA", exchange="NSE", sector="power_energy", industry="Financial Services", cap_tier="large_cap", fno_eligible=False, catalyst="Nodal agency status for renewable energy financing.", country="IN"),
        "RECLTD.NS": StockMeta(name="REC Limited", symbol="RECLTD", exchange="NSE", sector="power_energy", industry="Financial Services", cap_tier="large_cap", fno_eligible=True, catalyst="Diversification into non-power infrastructure lending.", country="IN"),
        "PFC.NS": StockMeta(name="Power Finance Corp", symbol="PFC", exchange="NSE", sector="power_energy", industry="Financial Services", cap_tier="large_cap", fno_eligible=True, catalyst="Strong asset quality metrics and robust loan growth.", country="IN"),
    }

    INFRASTRUCTURE: Dict[str, StockMeta] = {
        "LT.NS": StockMeta(name="Larsen & Toubro", symbol="LT", exchange="NSE", sector="infrastructure", industry="Construction", cap_tier="large_cap", fno_eligible=True, catalyst="Record order book from Middle East and domestic capex.", country="IN"),
        "ADANIENT.NS": StockMeta(name="Adani Enterprises", symbol="ADANIENT", exchange="NSE", sector="infrastructure", industry="Conglomerates", cap_tier="large_cap", fno_eligible=True, catalyst="Green hydrogen ecosystem and airport business scaling.", country="IN"),
        "ADANIPORTS.NS": StockMeta(name="Adani Ports", symbol="ADANIPORTS", exchange="NSE", sector="infrastructure", industry="Infrastructure", cap_tier="large_cap", fno_eligible=True, catalyst="Logistics expansion and market share gains in cargo handling.", country="IN"),
        "IRCON.NS": StockMeta(name="Ircon International", symbol="IRCON", exchange="NSE", sector="infrastructure", industry="Construction", cap_tier="mid_cap", fno_eligible=False, catalyst="Railway infrastructure spending and international projects.", country="IN"),
        "RVNL.NS": StockMeta(name="Rail Vikas Nigam", symbol="RVNL", exchange="NSE", sector="infrastructure", industry="Construction", cap_tier="mid_cap", fno_eligible=False, catalyst="Vande Bharat trainsets and metro project executions.", country="IN"),
        "RAILTEL.NS": StockMeta(name="RailTel Corporation", symbol="RAILTEL", exchange="NSE", sector="infrastructure", industry="Telecom Services", cap_tier="small_cap", fno_eligible=False, catalyst="Kavach signaling system implementation and broadband.", country="IN"),
        "TITAGARH.NS": StockMeta(name="Titagarh Rail Systems", symbol="TITAGARH", exchange="NSE", sector="infrastructure", industry="Manufacturing", cap_tier="small_cap", fno_eligible=False, catalyst="Wagon manufacturing orders and Pune Metro execution.", country="IN"),
        "IRFC.NS": StockMeta(name="Indian Railway Finance", symbol="IRFC", exchange="NSE", sector="infrastructure", industry="Financial Services", cap_tier="large_cap", fno_eligible=False, catalyst="Sole financing arm for massive railway capex.", country="IN"),
        "NBCC.NS": StockMeta(name="NBCC (India)", symbol="NBCC", exchange="NSE", sector="infrastructure", industry="Construction", cap_tier="mid_cap", fno_eligible=False, catalyst="Redevelopment projects and PMC business growth.", country="IN"),
        "NCC.NS": StockMeta(name="NCC Limited", symbol="NCC", exchange="NSE", sector="infrastructure", industry="Construction", cap_tier="small_cap", fno_eligible=False, catalyst="Jal Jeevan Mission orders and improving working capital.", country="IN"),
        "KEC.NS": StockMeta(name="KEC International", symbol="KEC", exchange="NSE", sector="infrastructure", industry="Construction", cap_tier="small_cap", fno_eligible=False, catalyst="T&D segment margins improvement and civil order book.", country="IN"),
        "THERMAX.NS": StockMeta(name="Thermax Limited", symbol="THERMAX", exchange="NSE", sector="infrastructure", industry="Machinery", cap_tier="mid_cap", fno_eligible=False, catalyst="Green energy solutions and industrial decarbonization.", country="IN"),
        "KALPATPOWR.NS": StockMeta(name="Kalpataru Projects", symbol="KALPATPOWR", exchange="NSE", sector="infrastructure", industry="Construction", cap_tier="mid_cap", fno_eligible=False, catalyst="JMC merger synergies and international T&D execution.", country="IN"),
        "ENGINERSIN.NS": StockMeta(name="Engineers India", symbol="ENGINERSIN", exchange="NSE", sector="infrastructure", industry="Consulting", cap_tier="small_cap", fno_eligible=False, catalyst="Hydrocarbon capex revival and green hydrogen consultancy.", country="IN"),
        "JKCEMENT.NS": StockMeta(name="JK Cement", symbol="JKCEMENT", exchange="NSE", sector="infrastructure", industry="Building Materials", cap_tier="mid_cap", fno_eligible=True, catalyst="Grey cement capacity expansion and white cement dominance.", country="IN"),
    }

    FMCG_CONSUMER: Dict[str, StockMeta] = {
        "HINDUNILVR.NS": StockMeta(name="Hindustan Unilever", symbol="HINDUNILVR", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Rural volume recovery and premiumization strategy.", country="IN"),
        "ITC.NS": StockMeta(name="ITC Limited", symbol="ITC", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Hotel business demerger and resilient cigarette volumes.", country="IN"),
        "NESTLEIND.NS": StockMeta(name="Nestle India", symbol="NESTLEIND", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Rurban penetration and millets/health portfolio push.", country="IN"),
        "BRITANNIA.NS": StockMeta(name="Britannia Industries", symbol="BRITANNIA", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Market share gains in hindi belt and dairy business scale-up.", country="IN"),
        "DABUR.NS": StockMeta(name="Dabur India", symbol="DABUR", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Healthcare portfolio resilience and Badshah Masala integration.", country="IN"),
        "MARICO.NS": StockMeta(name="Marico Limited", symbol="MARICO", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Copra price stability and food business diversification.", country="IN"),
        "GODREJCP.NS": StockMeta(name="Godrej Consumer", symbol="GODREJCP", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Raymond FMCG acquisition and Indonesia business turnaround.", country="IN"),
        "COLPAL.NS": StockMeta(name="Colgate-Palmolive", symbol="COLPAL", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Core toothpaste premiumization and personal care revamp.", country="IN"),
        "TATACONSUM.NS": StockMeta(name="Tata Consumer Products", symbol="TATACONSUM", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="large_cap", fno_eligible=True, catalyst="Capital Foods/Organic India acquisition integration.", country="IN"),
        "EMAMILTD.NS": StockMeta(name="Emami Limited", symbol="EMAMILTD", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="mid_cap", fno_eligible=False, catalyst="D2C investments and rural demand revival.", country="IN"),
        "RADICO.NS": StockMeta(name="Radico Khaitan", symbol="RADICO", exchange="NSE", sector="fmcg_consumer", industry="Beverages", cap_tier="mid_cap", fno_eligible=False, catalyst="Premium IMFL volume growth and raw material easing.", country="IN"),
        "VBL.NS": StockMeta(name="Varun Beverages", symbol="VBL", exchange="NSE", sector="fmcg_consumer", industry="Beverages", cap_tier="large_cap", fno_eligible=False, catalyst="South Africa acquisition and energy drink penetration.", country="IN"),
        "UNITDSPR.NS": StockMeta(name="United Spirits", symbol="UNITDSPR", exchange="NSE", sector="fmcg_consumer", industry="Beverages", cap_tier="large_cap", fno_eligible=True, catalyst="Prestige & Above segment focus and debt reduction.", country="IN"),
        "JYOTHYLAB.NS": StockMeta(name="Jyothy Labs", symbol="JYOTHYLAB", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="small_cap", fno_eligible=False, catalyst="Detergent market share gains and margin expansion.", country="IN"),
        "BIKAJI.NS": StockMeta(name="Bikaji Foods", symbol="BIKAJI", exchange="NSE", sector="fmcg_consumer", industry="FMCG", cap_tier="small_cap", fno_eligible=False, catalyst="PLI benefits and core market distribution depth.", country="IN"),
    }

    CHEMICALS_MATERIALS: Dict[str, StockMeta] = {
        "PIDILITE.NS": StockMeta(name="Pidilite Industries", symbol="PIDILITE", exchange="NSE", sector="chemicals_materials", industry="Specialty Chemicals", cap_tier="large_cap", fno_eligible=True, catalyst="VAM price softening and core adhesive volume growth.", country="IN"),
        "SRF.NS": StockMeta(name="SRF Limited", symbol="SRF", exchange="NSE", sector="chemicals_materials", industry="Specialty Chemicals", cap_tier="large_cap", fno_eligible=True, catalyst="Fluorospecialty capex commercialization and packaging margin recovery.", country="IN"),
        "AARTI.NS": StockMeta(name="Aarti Industries", symbol="AARTI", exchange="NSE", sector="chemicals_materials", industry="Specialty Chemicals", cap_tier="mid_cap", fno_eligible=True, catalyst="Long-term contracts ramp-up and nitro-toluene capacity.", country="IN"),
        "DEEPAKNITRO.NS": StockMeta(name="Deepak Nitrite", symbol="DEEPAKNITRO", exchange="NSE", sector="chemicals_materials", industry="Specialty Chemicals", cap_tier="mid_cap", fno_eligible=True, catalyst="Phenol import substitution and advanced intermediates capex.", country="IN"),
        "CLEAN.NS": StockMeta(name="Clean Science", symbol="CLEAN", exchange="NSE", sector="chemicals_materials", industry="Specialty Chemicals", cap_tier="small_cap", fno_eligible=False, catalyst="HALS series commercialization and green chemistry processes.", country="IN"),
        "ATUL.NS": StockMeta(name="Atul Limited", symbol="ATUL", exchange="NSE", sector="chemicals_materials", industry="Specialty Chemicals", cap_tier="mid_cap", fno_eligible=True, catalyst="Debottlenecking benefits and life science chemical growth.", country="IN"),
        "ULTRACEMCO.NS": StockMeta(name="UltraTech Cement", symbol="ULTRACEMCO", exchange="NSE", sector="chemicals_materials", industry="Building Materials", cap_tier="large_cap", fno_eligible=True, catalyst="Aggressive capacity expansion to 200 MTPA and Kesoram acquisition.", country="IN"),
        "GRASIM.NS": StockMeta(name="Grasim Industries", symbol="GRASIM", exchange="NSE", sector="chemicals_materials", industry="Building Materials", cap_tier="large_cap", fno_eligible=True, catalyst="Paints business launch and B2B e-commerce platform.", country="IN"),
        "RAMCOCEM.NS": StockMeta(name="The Ramco Cements", symbol="RAMCOCEM", exchange="NSE", sector="chemicals_materials", industry="Building Materials", cap_tier="mid_cap", fno_eligible=True, catalyst="Capacity utilization in AP/Odisha and premium product mix.", country="IN"),
        "JSWSTEEL.NS": StockMeta(name="JSW Steel", symbol="JSWSTEEL", exchange="NSE", sector="chemicals_materials", industry="Metals", cap_tier="large_cap", fno_eligible=True, catalyst="Brownfield expansions and value-added steel focus.", country="IN"),
        "TATASTEEL.NS": StockMeta(name="Tata Steel", symbol="TATASTEEL", exchange="NSE", sector="chemicals_materials", industry="Metals", cap_tier="large_cap", fno_eligible=True, catalyst="UK operations restructuring and India capacity additions.", country="IN"),
        "HINDALCO.NS": StockMeta(name="Hindalco Industries", symbol="HINDALCO", exchange="NSE", sector="chemicals_materials", industry="Metals", cap_tier="large_cap", fno_eligible=True, catalyst="Novelis beverage can demand recovery and EV battery foils.", country="IN"),
    }

    REAL_ESTATE: Dict[str, StockMeta] = {
        "DLF.NS": StockMeta(name="DLF Limited", symbol="DLF", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="large_cap", fno_eligible=True, catalyst="Robust luxury residential sales and strong office leasing.", country="IN"),
        "GODREJPROP.NS": StockMeta(name="Godrej Properties", symbol="GODREJPROP", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="large_cap", fno_eligible=True, catalyst="Aggressive business development and high launch pipeline.", country="IN"),
        "OBEROIRLTY.NS": StockMeta(name="Oberoi Realty", symbol="OBEROIRLTY", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="mid_cap", fno_eligible=True, catalyst="Thane project launch and mall portfolio expansion.", country="IN"),
        "PHOENIXLTD.NS": StockMeta(name="Phoenix Mills", symbol="PHOENIXLTD", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="mid_cap", fno_eligible=False, catalyst="Strong consumption at new malls and commercial asset scale-up.", country="IN"),
        "PRESTIGE.NS": StockMeta(name="Prestige Estates", symbol="PRESTIGE", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="mid_cap", fno_eligible=False, catalyst="Geographic diversification to Mumbai/NCR and robust presales.", country="IN"),
        "BRIGADE.NS": StockMeta(name="Brigade Enterprises", symbol="BRIGADE", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="small_cap", fno_eligible=False, catalyst="Chennai/Hyderabad expansion and hospitality revival.", country="IN"),
        "SOBHA.NS": StockMeta(name="Sobha Limited", symbol="SOBHA", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="small_cap", fno_eligible=False, catalyst="Rights issue deleveraging and realization improvement.", country="IN"),
        "SUNTECK.NS": StockMeta(name="Sunteck Realty", symbol="SUNTECK", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="small_cap", fno_eligible=False, catalyst="Asset-light JDA model and mid-income segment focus.", country="IN"),
        "MAHLIFE.NS": StockMeta(name="Mahindra Lifespace", symbol="MAHLIFE", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="small_cap", fno_eligible=False, catalyst="IC&IC business monetization and urban development pipeline.", country="IN"),
        "LODHA.NS": StockMeta(name="Macrotech Developers", symbol="LODHA", exchange="NSE", sector="real_estate", industry="Real Estate", cap_tier="large_cap", fno_eligible=False, catalyst="Significant debt reduction and strong execution track record.", country="IN"),
    }

    US_TECH: Dict[str, StockMeta] = {
        "AAPL": StockMeta(name="Apple Inc.", symbol="AAPL", exchange="NASDAQ", sector="us_tech", industry="Consumer Electronics", cap_tier="large_cap", fno_eligible=False, catalyst="Generative AI integration in iOS 18 and Services growth.", country="US"),
        "MSFT": StockMeta(name="Microsoft Corporation", symbol="MSFT", exchange="NASDAQ", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Copilot monetization and Azure AI workload growth.", country="US"),
        "NVDA": StockMeta(name="NVIDIA Corporation", symbol="NVDA", exchange="NASDAQ", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="Blackwell GPU architecture ramp and data center dominance.", country="US"),
        "GOOGL": StockMeta(name="Alphabet Inc.", symbol="GOOGL", exchange="NASDAQ", sector="us_tech", industry="Internet Content", cap_tier="large_cap", fno_eligible=False, catalyst="Gemini AI multimodal capabilities and YouTube Shorts monetization.", country="US"),
        "META": StockMeta(name="Meta Platforms", symbol="META", exchange="NASDAQ", sector="us_tech", industry="Internet Content", cap_tier="large_cap", fno_eligible=False, catalyst="Advantage+ AI advertising efficiency and Reels engagement.", country="US"),
        "AMZN": StockMeta(name="Amazon.com", symbol="AMZN", exchange="NASDAQ", sector="us_tech", industry="E-commerce", cap_tier="large_cap", fno_eligible=False, catalyst="AWS stabilization and retail operating margin expansion.", country="US"),
        "TSLA": StockMeta(name="Tesla, Inc.", symbol="TSLA", exchange="NASDAQ", sector="us_tech", industry="Automobiles", cap_tier="large_cap", fno_eligible=False, catalyst="FSD V12 adoption and Robotaxi network launch.", country="US"),
        "CRM": StockMeta(name="Salesforce, Inc.", symbol="CRM", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Einstein Copilot traction and strict margin discipline.", country="US"),
        "ADBE": StockMeta(name="Adobe Inc.", symbol="ADBE", exchange="NASDAQ", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Firefly AI integration pricing power and Creative Cloud retention.", country="US"),
        "ORCL": StockMeta(name="Oracle Corporation", symbol="ORCL", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="OCI Gen2 cloud growth and AI infrastructure partnerships.", country="US"),
        "NOW": StockMeta(name="ServiceNow, Inc.", symbol="NOW", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Pro Plus AI SKU adoption and IT service management dominance.", country="US"),
        "SNOW": StockMeta(name="Snowflake Inc.", symbol="SNOW", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Cortex AI features and transition to Iceberg tables.", country="US"),
        "PLTR": StockMeta(name="Palantir Technologies", symbol="PLTR", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="AIP bootcamps driving strong US commercial customer acquisition.", country="US"),
        "CRWD": StockMeta(name="CrowdStrike Holdings", symbol="CRWD", exchange="NASDAQ", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Platform consolidation and Charlotte AI adoption.", country="US"),
        "DDOG": StockMeta(name="Datadog, Inc.", symbol="DDOG", exchange="NASDAQ", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Cloud optimization stabilization and AI-native app monitoring.", country="US"),
        "AMD": StockMeta(name="Advanced Micro Devices", symbol="AMD", exchange="NASDAQ", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="MI300X AI accelerator ramp and server CPU share gains.", country="US"),
        "INTC": StockMeta(name="Intel Corporation", symbol="INTC", exchange="NASDAQ", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="Foundry model transition and AI PC processor launch.", country="US"),
        "QCOM": StockMeta(name="QUALCOMM Incorporated", symbol="QCOM", exchange="NASDAQ", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="Snapdragon X Elite for AI PCs and smartphone inventory normalisation.", country="US"),
        "AVGO": StockMeta(name="Broadcom Inc.", symbol="AVGO", exchange="NASDAQ", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="Custom AI silicon demand and VMware integration synergies.", country="US"),
        "MU": StockMeta(name="Micron Technology", symbol="MU", exchange="NASDAQ", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="HBM3E memory capacity constraints and pricing power.", country="US"),
        "ARM": StockMeta(name="Arm Holdings", symbol="ARM", exchange="NASDAQ", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="v9 architecture adoption and data center penetration.", country="US"),
        "TSM": StockMeta(name="Taiwan Semiconductor", symbol="TSM", exchange="NYSE", sector="us_tech", industry="Semiconductors", cap_tier="large_cap", fno_eligible=False, catalyst="3nm process node leadership and AI chip fabrication monopoly.", country="US"),
        "NFLX": StockMeta(name="Netflix, Inc.", symbol="NFLX", exchange="NASDAQ", sector="us_tech", industry="Entertainment", cap_tier="large_cap", fno_eligible=False, catalyst="Ad-tier scale-up and live sports broadcasting initiatives.", country="US"),
        "DIS": StockMeta(name="Walt Disney Company", symbol="DIS", exchange="NYSE", sector="us_tech", industry="Entertainment", cap_tier="large_cap", fno_eligible=False, catalyst="Streaming profitability focus and parks segment resilience.", country="US"),
        "UBER": StockMeta(name="Uber Technologies", symbol="UBER", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Mobility margin expansion and advertising business growth.", country="US"),
        "ABNB": StockMeta(name="Airbnb, Inc.", symbol="ABNB", exchange="NASDAQ", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="International expansion and platform reliability improvements.", country="US"),
        "SHOP": StockMeta(name="Shopify Inc.", symbol="SHOP", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Enterprise merchant adoption and logistics business divestiture.", country="US"),
        "SPOT": StockMeta(name="Spotify Technology", symbol="SPOT", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Audiobooks integration and aggressive cost-cutting measures.", country="US"),
        "RBLX": StockMeta(name="Roblox Corporation", symbol="RBLX", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="large_cap", fno_eligible=False, catalyst="Aging up user base and programmatic video ads launch.", country="US"),
        "SNAP": StockMeta(name="Snap Inc.", symbol="SNAP", exchange="NYSE", sector="us_tech", industry="Software", cap_tier="mid_cap", fno_eligible=False, catalyst="Direct response ad platform rebuild and Snapchat+ subscriptions.", country="US"),
    }

    US_FINANCE: Dict[str, StockMeta] = {
        "JPM": StockMeta(name="JPMorgan Chase", symbol="JPM", exchange="NYSE", sector="us_finance", industry="Banks", cap_tier="large_cap", fno_eligible=False, catalyst="First Republic integration and strong net interest income.", country="US"),
        "GS": StockMeta(name="Goldman Sachs", symbol="GS", exchange="NYSE", sector="us_finance", industry="Capital Markets", cap_tier="large_cap", fno_eligible=False, catalyst="Investment banking rebound and consumer business exit.", country="US"),
        "MS": StockMeta(name="Morgan Stanley", symbol="MS", exchange="NYSE", sector="us_finance", industry="Capital Markets", cap_tier="large_cap", fno_eligible=False, catalyst="Wealth management recurring revenue and asset gathering.", country="US"),
        "BAC": StockMeta(name="Bank of America", symbol="BAC", exchange="NYSE", sector="us_finance", industry="Banks", cap_tier="large_cap", fno_eligible=False, catalyst="Unrealized bond loss stabilization and expense management.", country="US"),
        "WFC": StockMeta(name="Wells Fargo", symbol="WFC", exchange="NYSE", sector="us_finance", industry="Banks", cap_tier="large_cap", fno_eligible=False, catalyst="Asset cap removal progress and efficiency initiatives.", country="US"),
        "C": StockMeta(name="Citigroup Inc.", symbol="C", exchange="NYSE", sector="us_finance", industry="Banks", cap_tier="large_cap", fno_eligible=False, catalyst="Global wealth restructuring and international consumer exits.", country="US"),
        "V": StockMeta(name="Visa Inc.", symbol="V", exchange="NYSE", sector="us_finance", industry="Financial Services", cap_tier="large_cap", fno_eligible=False, catalyst="Cross-border travel recovery and value-added services growth.", country="US"),
        "MA": StockMeta(name="Mastercard", symbol="MA", exchange="NYSE", sector="us_finance", industry="Financial Services", cap_tier="large_cap", fno_eligible=False, catalyst="B2B payments expansion and cybersecurity services.", country="US"),
        "PYPL": StockMeta(name="PayPal Holdings", symbol="PYPL", exchange="NASDAQ", sector="us_finance", industry="Financial Services", cap_tier="large_cap", fno_eligible=False, catalyst="Braintree margin improvement and unbranded checkout focus.", country="US"),
        "AXP": StockMeta(name="American Express", symbol="AXP", exchange="NYSE", sector="us_finance", industry="Consumer Finance", cap_tier="large_cap", fno_eligible=False, catalyst="Millennial/Gen Z customer acquisition and fee income growth.", country="US"),
        "BLK": StockMeta(name="BlackRock, Inc.", symbol="BLK", exchange="NYSE", sector="us_finance", industry="Asset Management", cap_tier="large_cap", fno_eligible=False, catalyst="Private markets expansion via GIP acquisition and Bitcoin ETF.", country="US"),
        "SCHW": StockMeta(name="Charles Schwab", symbol="SCHW", exchange="NYSE", sector="us_finance", industry="Capital Markets", cap_tier="large_cap", fno_eligible=False, catalyst="Client cash sorting normalization and TD Ameritrade integration.", country="US"),
        "BRK-B": StockMeta(name="Berkshire Hathaway", symbol="BRK-B", exchange="NYSE", sector="us_finance", industry="Insurance", cap_tier="large_cap", fno_eligible=False, catalyst="Geico underwriting turnaround and strong cash deployment.", country="US"),
        "SOFI": StockMeta(name="SoFi Technologies", symbol="SOFI", exchange="NASDAQ", sector="us_finance", industry="Consumer Finance", cap_tier="small_cap", fno_eligible=False, catalyst="GAAP profitability milestone and tech platform segment growth.", country="US"),
        "COIN": StockMeta(name="Coinbase Global", symbol="COIN", exchange="NASDAQ", sector="us_finance", industry="Capital Markets", cap_tier="large_cap", fno_eligible=False, catalyst="Spot ETF custody fees and Base Layer 2 network adoption.", country="US"),
    }

    US_HEALTHCARE: Dict[str, StockMeta] = {
        "JNJ": StockMeta(name="Johnson & Johnson", symbol="JNJ", exchange="NYSE", sector="us_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=False, catalyst="Kenvue spin-off focus on medtech and innovative medicine.", country="US"),
        "UNH": StockMeta(name="UnitedHealth Group", symbol="UNH", exchange="NYSE", sector="us_healthcare", industry="Healthcare Plans", cap_tier="large_cap", fno_eligible=False, catalyst="Optum Health value-based care expansion and Medicare Advantage growth.", country="US"),
        "LLY": StockMeta(name="Eli Lilly", symbol="LLY", exchange="NYSE", sector="us_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=False, catalyst="Mounjaro/Zepbound GLP-1 weight loss dominance and Alzheimer's pipeline.", country="US"),
        "PFE": StockMeta(name="Pfizer Inc.", symbol="PFE", exchange="NYSE", sector="us_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=False, catalyst="Seagen acquisition integration for oncology portfolio revamp.", country="US"),
        "ABBV": StockMeta(name="AbbVie Inc.", symbol="ABBV", exchange="NYSE", sector="us_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=False, catalyst="Skyrizi and Rinvoq offsetting Humira biosimilar competition.", country="US"),
        "MRK": StockMeta(name="Merck & Co.", symbol="MRK", exchange="NYSE", sector="us_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=False, catalyst="Keytruda label expansions and Prometheus Biosciences acquisition.", country="US"),
        "AMGN": StockMeta(name="Amgen Inc.", symbol="AMGN", exchange="NASDAQ", sector="us_healthcare", industry="Biotechnology", cap_tier="large_cap", fno_eligible=False, catalyst="Horizon Therapeutics rare disease portfolio integration.", country="US"),
        "GILD": StockMeta(name="Gilead Sciences", symbol="GILD", exchange="NASDAQ", sector="us_healthcare", industry="Biotechnology", cap_tier="large_cap", fno_eligible=False, catalyst="Trodelvy oncology growth and long-acting HIV treatments.", country="US"),
        "MRNA": StockMeta(name="Moderna, Inc.", symbol="MRNA", exchange="NASDAQ", sector="us_healthcare", industry="Biotechnology", cap_tier="large_cap", fno_eligible=False, catalyst="RSV vaccine launch and personalized cancer vaccine data.", country="US"),
        "NVO": StockMeta(name="Novo Nordisk", symbol="NVO", exchange="NYSE", sector="us_healthcare", industry="Pharmaceuticals", cap_tier="large_cap", fno_eligible=False, catalyst="Wegovy manufacturing scale-up and cardiovascular outcome trial data.", country="US"),
        "TMO": StockMeta(name="Thermo Fisher", symbol="TMO", exchange="NYSE", sector="us_healthcare", industry="Medical Devices", cap_tier="large_cap", fno_eligible=False, catalyst="Bioproduction destocking recovery and Olink acquisition.", country="US"),
        "ISRG": StockMeta(name="Intuitive Surgical", symbol="ISRG", exchange="NASDAQ", sector="us_healthcare", industry="Medical Devices", cap_tier="large_cap", fno_eligible=False, catalyst="da Vinci 5 system launch and procedure volume recovery.", country="US"),
    }

    _ALL_UNIVERSES = {
        "banking_financial": BANKING_FINANCIAL,
        "it_software": IT_SOFTWARE,
        "pharma_healthcare": PHARMA_HEALTHCARE,
        "auto_ancillaries": AUTO_ANCILLARIES,
        "gems_jewellery": GEMS_JEWELLERY,
        "textiles_apparel": TEXTILES_APPAREL,
        "defence_aerospace": DEFENCE_AEROSPACE,
        "power_energy": POWER_ENERGY,
        "infrastructure": INFRASTRUCTURE,
        "fmcg_consumer": FMCG_CONSUMER,
        "chemicals_materials": CHEMICALS_MATERIALS,
        "real_estate": REAL_ESTATE,
        "us_tech": US_TECH,
        "us_finance": US_FINANCE,
        "us_healthcare": US_HEALTHCARE,
    }

    # ─── Sector Alias Normalization ─────────────────────────────────────────────
    _SECTOR_ALIASES: dict[str, str] = {
        # Banking & Financial
        "banking": "banking_financial", "bank": "banking_financial", "banks": "banking_financial",
        "finance": "banking_financial", "financial": "banking_financial", "nbfc": "banking_financial",
        "lending": "banking_financial", "insurance": "banking_financial",
        # IT & Software
        "it": "it_software", "software": "it_software", "tech": "it_software",
        "technology": "it_software", "digital": "it_software",
        # Pharma & Healthcare
        "pharma": "pharma_healthcare", "healthcare": "pharma_healthcare", "health": "pharma_healthcare",
        "hospital": "pharma_healthcare", "medicine": "pharma_healthcare", "drug": "pharma_healthcare",
        # Auto & Ancillaries
        "auto": "auto_ancillaries", "automobile": "auto_ancillaries", "vehicle": "auto_ancillaries",
        "car": "auto_ancillaries", "motor": "auto_ancillaries", "tyre": "auto_ancillaries",
        # Gems & Jewellery
        "jewellery": "gems_jewellery", "jewelry": "gems_jewellery", "gems": "gems_jewellery",
        "jewel": "gems_jewellery", "gem": "gems_jewellery", "ornament": "gems_jewellery",
        "gold stock": "gems_jewellery", "diamond": "gems_jewellery",
        # Textiles & Apparel
        "textiles": "textiles_apparel", "textile": "textiles_apparel", "apparel": "textiles_apparel",
        "garment": "textiles_apparel", "garments": "textiles_apparel", "clothing": "textiles_apparel",
        "cloth": "textiles_apparel", "fabric": "textiles_apparel", "cotton": "textiles_apparel",
        "yarn": "textiles_apparel",
        # Defence & Aerospace
        "defence": "defence_aerospace", "defense": "defence_aerospace", "aerospace": "defence_aerospace",
        "military": "defence_aerospace",
        # Power & Energy
        "power": "power_energy", "energy": "power_energy", "renewable": "power_energy",
        "solar": "power_energy", "wind": "power_energy", "utility": "power_energy",
        # Infrastructure
        "infra": "infrastructure", "construction": "infrastructure", "cement": "infrastructure",
        "railway": "infrastructure", "railways": "infrastructure",
        # FMCG & Consumer
        "fmcg": "fmcg_consumer", "consumer": "fmcg_consumer", "retail": "fmcg_consumer",
        "beverage": "fmcg_consumer",
        # Chemicals & Materials
        "chemical": "chemicals_materials", "chemicals": "chemicals_materials",
        "material": "chemicals_materials", "materials": "chemicals_materials",
        "metal": "chemicals_materials", "metals": "chemicals_materials",
        "steel": "chemicals_materials", "paint": "chemicals_materials",
        # Real Estate
        "real estate": "real_estate", "realty": "real_estate", "property": "real_estate",
        "housing": "real_estate",
        # US sectors
        "us tech": "us_tech", "us technology": "us_tech", "american tech": "us_tech",
        "us finance": "us_finance", "us banking": "us_finance", "american bank": "us_finance",
        "us health": "us_healthcare", "us pharma": "us_healthcare", "american pharma": "us_healthcare",
    }

    _SECTOR_DISPLAY_NAMES: dict[str, str] = {
        "banking_financial": "Banking & Financial",
        "it_software": "IT & Software",
        "pharma_healthcare": "Pharma & Healthcare",
        "auto_ancillaries": "Automobile & Auto Components",
        "gems_jewellery": "Gems & Jewellery",
        "textiles_apparel": "Textiles & Apparel",
        "defence_aerospace": "Defence & Aerospace",
        "power_energy": "Power & Energy",
        "infrastructure": "Infrastructure & Capital Goods",
        "fmcg_consumer": "FMCG & Consumer",
        "chemicals_materials": "Chemicals & Materials",
        "real_estate": "Real Estate",
        "us_tech": "US Technology",
        "us_finance": "US Financials",
        "us_healthcare": "US Healthcare",
    }

    @classmethod
    def _normalize_sector(cls, sector: Optional[str]) -> Optional[str]:
        """Normalize a sector alias to the canonical internal key."""
        if not sector:
            return None
        sector_lower = sector.strip().lower()
        # Already a canonical key
        if sector_lower in cls._ALL_UNIVERSES:
            return sector_lower
        # Lookup alias
        if sector_lower in cls._SECTOR_ALIASES:
            return cls._SECTOR_ALIASES[sector_lower]
        return sector_lower  # Return as-is; get_universe will handle missing keys gracefully

    @classmethod
    def get_sector_display_name(cls, sector: Optional[str]) -> str:
        """Return human-readable display name for a sector key or comma-separated keys."""
        if not sector:
            return "Indian Equity"
        parts = [s.strip() for s in sector.split(",") if s.strip()]
        display_names: list[str] = []
        for p in parts:
            norm = cls._normalize_sector(p)
            name = cls._SECTOR_DISPLAY_NAMES.get(norm, p.replace("_", " ").title())
            if name not in display_names:
                display_names.append(name)
        return " & ".join(display_names) if display_names else "Indian Equity"

    @classmethod
    def get_universe(cls, sector: str = None, cap_tier: str = None, exchange: str = None) -> Dict[str, StockMeta]:
        """
        Get the stock universe, optionally filtered by sector(s), cap_tier, and exchange.
        Supports alias normalization and comma-separated multi-sector strings (e.g. 'textiles,gems_jewellery').
        """
        universe: Dict[str, StockMeta] = {}

        sectors_to_fetch: list[str] = []
        if sector:
            raw_parts = [s.strip() for s in sector.split(",") if s.strip()]
            for part in raw_parts:
                norm = cls._normalize_sector(part)
                if norm and norm in cls._ALL_UNIVERSES:
                    if norm not in sectors_to_fetch:
                        sectors_to_fetch.append(norm)
                elif norm:
                    # Sector recognized but no dedicated universe dictionary
                    logger.debug("Sector '%s' normalized to '%s' but not found in _ALL_UNIVERSES", part, norm)
        else:
            sectors_to_fetch = list(cls._ALL_UNIVERSES.keys())

        for sec in sectors_to_fetch:
            if sec in cls._ALL_UNIVERSES:
                for symbol, meta in cls._ALL_UNIVERSES[sec].items():
                    if cap_tier and meta.cap_tier != cap_tier:
                        continue
                    if exchange and meta.exchange != exchange:
                        continue
                    universe[symbol] = meta

        return universe

    @classmethod
    def get_all_sectors(cls) -> List[str]:
        """
        Get a list of all available sectors.
        """
        return list(cls._ALL_UNIVERSES.keys())

    @classmethod
    def get_sector_for_query(cls, query: str) -> Optional[str]:
        """
        Detects sector(s) from natural language query using regex patterns.
        If multiple sectors are detected (e.g. 'textiles, gems and jewellery'),
        returns them as a comma-separated string preserving order of appearance.
        """
        query_low = query.lower()

        patterns = {
            "banking_financial": r"\b(bank|banking|banks|finance|financial|financials|nbfc|lending|insurance)\b",
            "it_software": r"\b(it|tech|technology|software|digital)\b",
            "pharma_healthcare": r"\b(pharma|pharmaceutical|pharmaceuticals|health|healthcare|hospital|hospitals|medicine|drug|drugs)\b",
            "auto_ancillaries": r"\b(auto|automobile|automotive|vehicle|vehicles|car|cars|motor|ancillary|ancillaries|tyre|tyres)\b",
            "gems_jewellery": r"\b(jewel|jewels|jewellery|jewelry|gem|gems|gold|diamond|diamonds|ornament|ornaments)\b",
            "textiles_apparel": r"\b(textile|textiles|apparel|garment|garments|clothing|cloth|fabric|fabrics|cotton|yarn)\b",
            "defence_aerospace": r"\b(defence|defense|aerospace|military)\b",
            "power_energy": r"\b(power|energy|renewable|renewables|solar|wind|utility|utilities)\b",
            "infrastructure": r"\b(infra|infrastructure|construction|cement|railway|railways|building)\b",
            "fmcg_consumer": r"\b(fmcg|consumer|retail|beverage|beverages)\b",
            "chemicals_materials": r"\b(chemical|chemicals|material|materials|metal|metals|steel|paint|paints)\b",
            "real_estate": r"\b(real\s*estate|realty|property|properties|housing)\b",
            "us_tech": r"\b(us\s*tech|american\s*tech|nasdaq|us\s*software)\b",
            "us_finance": r"\b(us\s*finance|american\s*bank|us\s*bank)\b",
            "us_healthcare": r"\b(us\s*health|american\s*pharma|us\s*pharma)\b"
        }

        matched_sectors: list[str] = []
        is_us_query = ("us " in query_low) or ("american " in query_low)

        for sector, pattern in patterns.items():
            if re.search(pattern, query_low):
                if is_us_query:
                    if sector.startswith("us_"):
                        if sector not in matched_sectors:
                            matched_sectors.append(sector)
                else:
                    if not sector.startswith("us_"):
                        if sector not in matched_sectors:
                            matched_sectors.append(sector)

        if not matched_sectors:
            return None

        return ",".join(matched_sectors)

    @classmethod
    def get_stock_meta(cls, symbol: str) -> Optional[StockMeta]:
        """
        Get metadata for a specific stock symbol.
        """
        for sector_dict in cls._ALL_UNIVERSES.values():
            if symbol in sector_dict:
                return sector_dict[symbol]
        return None

    @classmethod
    def get_legacy_universe(cls, cap_tier: str = None) -> Dict[str, dict]:
        """
        Returns the universe in the legacy format used by finance.py.
        """
        legacy_universe = {}
        for sector_dict in cls._ALL_UNIVERSES.values():
            for symbol, meta in sector_dict.items():
                if cap_tier and meta.cap_tier != cap_tier:
                    continue
                legacy_universe[symbol] = {
                    "name": meta.name,
                    "sector": meta.sector,
                    "symbol": meta.symbol,
                    "catalyst": meta.catalyst
                }
        return legacy_universe

    @classmethod
    def get_fno_stocks(cls) -> Dict[str, StockMeta]:
        """
        Returns all stocks that are eligible for F&O.
        """
        fno_universe = {}
        for sector_dict in cls._ALL_UNIVERSES.values():
            for symbol, meta in sector_dict.items():
                if meta.fno_eligible:
                    fno_universe[symbol] = meta
        return fno_universe

    # ─── Canonical Sector Benchmark Indices ───────────────────────────────────
    NSE_SECTOR_INDICES: Dict[str, dict] = {
        "banking_financial": {"name": "NIFTY Bank", "symbol": "^NSEBANK", "display_name": "Banking & Financial Services", "sector": "banking_financial"},
        "it_software": {"name": "NIFTY IT", "symbol": "^CNXIT", "display_name": "Information Technology", "sector": "it_software"},
        "pharma_healthcare": {"name": "NIFTY Pharma", "symbol": "^CNXPHARMA", "display_name": "Pharmaceuticals & Healthcare", "sector": "pharma_healthcare"},
        "auto_ancillaries": {"name": "NIFTY Auto", "symbol": "^CNXAUTO", "display_name": "Automobile & Auto Components", "sector": "auto_ancillaries"},
        "fmcg_consumer": {"name": "NIFTY FMCG", "symbol": "^CNXFMCG", "display_name": "Fast Moving Consumer Goods", "sector": "fmcg_consumer"},
        "chemicals_materials": {"name": "NIFTY Metal", "symbol": "^CNXMETAL", "display_name": "Metals & Materials", "sector": "chemicals_materials"},
        "power_energy": {"name": "NIFTY Energy", "symbol": "^CNXENERGY", "display_name": "Power & Energy", "sector": "power_energy"},
        "real_estate": {"name": "NIFTY Realty", "symbol": "^CNXREALTY", "display_name": "Real Estate & Realty", "sector": "real_estate"},
        "infrastructure": {"name": "NIFTY Infra", "symbol": "^CNXINFRA", "display_name": "Infrastructure & Capital Goods", "sector": "infrastructure"},
    }

    US_SECTOR_INDICES: Dict[str, dict] = {
        "us_tech": {"name": "Technology Select Sector SPDR", "symbol": "XLK", "display_name": "US Technology", "sector": "us_tech"},
        "us_finance": {"name": "Financial Select Sector SPDR", "symbol": "XLF", "display_name": "US Financials", "sector": "us_finance"},
        "us_healthcare": {"name": "Health Care Select Sector SPDR", "symbol": "XLV", "display_name": "US Healthcare", "sector": "us_healthcare"},
    }

    @classmethod
    def get_sector_indices(cls, exchange: str = "NSE") -> Dict[str, dict]:
        """Return benchmark sector indices for the specified exchange."""
        if exchange and exchange.upper() in ("NYSE", "NASDAQ", "US"):
            return cls.US_SECTOR_INDICES
        return cls.NSE_SECTOR_INDICES

    @classmethod
    def get_sector_constituents(cls, sector: str) -> Dict[str, StockMeta]:
        """Return all stocks strictly mapped to the given sector."""
        return cls._ALL_UNIVERSES.get(sector, {})

    @classmethod
    def get_sector_index_ticker(cls, sector: str, exchange: str = "NSE") -> Optional[str]:
        """Return the benchmark index symbol for a sector."""
        indices = cls.get_sector_indices(exchange)
        entry = indices.get(sector)
        return entry["symbol"] if entry else None
