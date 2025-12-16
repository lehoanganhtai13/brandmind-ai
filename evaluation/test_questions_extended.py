"""
Extended Marketing Knowledge Test Questions

35 additional questions focusing on logical thinking and marketing principles,
NOT specific case studies. Questions test conceptual understanding and application.

Source: Principles of Marketing 17th Edition - Kotler & Armstrong
Generated from: docs/evaluation/generating_tests_2.md
"""

EXTENDED_TEST_QUESTIONS = [
    # ===========================================================================
    # CHAPTER 1: MARKETING FUNDAMENTALS (5 questions)
    # ===========================================================================
    {
        "id": "Q21",
        "level": "medium",
        "question": "Tại sao việc 'set the right level of expectations' lại quan trọng trong marketing?",
        "ground_truth": (
            "Set expectations quá thấp → satisfy khách mua nhưng không attract đủ buyers. "
            "Set expectations quá cao → buyers disappointed. Cả hai đều harmful cho customer "
            "relationships và brand reputation. Marketers cần balance để maximize cả acquisition "
            "và satisfaction."
        ),
        "source": "Chapter 1, Customer Value and Satisfaction",
    },
    {
        "id": "Q22",
        "level": "medium",
        "question": "Phân biệt Customer Relationship Management (CRM) với customer-engagement marketing",
        "ground_truth": (
            "CRM focus vào overall process building/maintaining profitable relationships bằng cách "
            "deliver superior value. Customer-engagement marketing là approach mới hơn, foster direct "
            "engagement với customers through branded content, dialogue, và co-creation experiences, "
            "thường qua digital/social media. CRM là broader strategy, engagement marketing là tactics hiện đại."
        ),
        "source": "Chapter 1, Engaging Customers and Managing Customer Relationships",
    },
    {
        "id": "Q23",
        "level": "medium",
        "question": "Giải thích khái niệm 'share of customer' và tại sao nó quan trọng?",
        "ground_truth": (
            "Share of customer là phần chi tiêu khách hàng dành cho brand so với total spending trong "
            "category đó. Quan trọng vì: (1) dễ hơn tăng purchase từ existing customers hơn acquire new ones, "
            "(2) increase profitability, (3) build loyalty. Strategies: cross-selling, up-selling, deepening relationships."
        ),
        "source": "Chapter 1, Capturing Value from Customers",
    },
    {
        "id": "Q24",
        "level": "medium",
        "question": "Khi nào công ty nên dùng 'selling concept' thay vì 'marketing concept'?",
        "ground_truth": (
            "Selling concept phù hợp khi: (1) company có overcapacity/excess inventory cần clear, "
            "(2) products là unsought goods (bảo hiểm, mộ phần), (3) short-term sales goals. "
            "Tuy nhiên, risk là ignore customer needs, chỉ focus transaction chứ không build long-term relationships."
        ),
        "source": "Chapter 1, Customer Value-Driven Marketing Strategy",
    },
    {
        "id": "Q25",
        "level": "medium",
        "question": "Exchange relationship cần điều kiện gì để xảy ra?",
        "ground_truth": (
            "Cần: (1) ít nhất 2 parties, (2) mỗi party có something of value với party kia, "
            "(3) khả năng communicate và deliver, (4) freedom to accept/reject offer, "
            "(5) desire to deal với party kia. Marketing occurs khi people satisfy needs through exchange relationships."
        ),
        "source": "Chapter 1, Exchanges and Relationships",
    },
    # ===========================================================================
    # CHAPTER 2: STRATEGIC PLANNING (5 questions)
    # ===========================================================================
    {
        "id": "Q26",
        "level": "medium",
        "question": "Tại sao một số companies cần downsize portfolio thay vì chỉ focus vào growth?",
        "ground_truth": (
            "Downsize cần thiết khi: (1) resources bị spread too thin, (2) brands không fit overall strategy, "
            "(3) unprofitable businesses consume disproportionate management attention, "
            "(4) changing environment làm products outdated. Divesting cho phép focus resources vào strongest opportunities."
        ),
        "source": "Chapter 2, Developing Strategies for Growth and Downsizing",
    },
    {
        "id": "Q27",
        "level": "medium",
        "question": "Sự khác biệt giữa strategic plan và marketing plan là gì?",
        "ground_truth": (
            "Strategic plan: corporate-level, defines overall mission/objectives, business portfolio decisions, "
            "long-term direction. Marketing plan: business-unit level, details specific marketing strategies/tactics (4Ps), "
            "action programs, implementation. Strategic plan guides marketing plan; marketing plan supports strategic plan "
            "với detailed execution."
        ),
        "source": "Chapter 2, Company-Wide Strategic Planning",
    },
    {
        "id": "Q28",
        "level": "medium",
        "question": "Tại sao interdepartmental conflicts xảy ra khi marketing tries to improve customer satisfaction?",
        "ground_truth": (
            "Marketing actions để improve satisfaction có thể: increase purchasing costs (better materials), "
            "disrupt production schedules (customization), increase inventories (more variety), "
            "create budget headaches (additional spending). Other departments resist vì làm họ perform worse "
            "in 'their terms.' Cần coordination để balance."
        ),
        "source": "Chapter 2, Partnering with Other Company Departments",
    },
    {
        "id": "Q29",
        "level": "medium",
        "question": "Khi nào nên dùng market development thay vì product development trong expansion strategy?",
        "ground_truth": (
            "Market development (new markets, existing products): khi có untapped segments/geographies, "
            "product proven successful, less R&D risk. Product development (new products, existing markets): "
            "khi current products aging, customer needs evolving, strong R&D capabilities. "
            "Decision depends on resources, risks, và market opportunities."
        ),
        "source": "Chapter 2, Product/Market Expansion Grid",
    },
    {
        "id": "Q30",
        "level": "medium",
        "question": "Tại sao value delivery network quan trọng hơn individual company performance?",
        "ground_truth": (
            "Vì competition không chỉ giữa individual companies mà giữa entire value delivery networks. "
            "Even if company makes best products, nó có thể lose nếu dealers/suppliers/partners provide poor experience. "
            "Customer satisfaction phụ thuộc vào entire system performance, không chỉ 1 entity."
        ),
        "source": "Chapter 2, Partnering with Others in the Marketing System",
    },
    # ===========================================================================
    # CHAPTER 3: MARKETING ENVIRONMENT (5 questions)
    # ===========================================================================
    {
        "id": "Q31",
        "level": "medium",
        "question": "Phân biệt microenvironment và macroenvironment, cho examples",
        "ground_truth": (
            "Microenvironment: forces gần company, có thể influence được phần nào - company, suppliers, "
            "intermediaries, customers, competitors, publics. Macroenvironment: broader forces, largely uncontrollable - "
            "demographic, economic, natural, technological, political/legal, cultural. "
            "Micro affects immediate operations; macro shapes long-term opportunities/threats."
        ),
        "source": "Chapter 3, The Microenvironment and Macroenvironment",
    },
    {
        "id": "Q32",
        "level": "medium",
        "question": "Tại sao demographic trends lại quan trọng nhất cho marketers?",
        "ground_truth": (
            "Vì 'people make up markets.' Demographic changes trực tiếp impact market size, composition, needs. "
            "Changes trong age structure, family composition, geographic shifts, education, diversity = changes in "
            "customer needs và buying behaviors. Marketers must track để identify opportunities và adapt strategies."
        ),
        "source": "Chapter 3, The Demographic Environment",
    },
    {
        "id": "Q33",
        "level": "medium",
        "question": "Reactive vs proactive approach to marketing environment - ưu nhược điểm?",
        "ground_truth": (
            "Reactive: wait và respond to changes. Ưu: safe, less risky. Nhược: miss opportunities, always behind. "
            "Proactive: take aggressive actions to shape environment. Ưu: create opportunities, competitive advantage. "
            "Nhược: higher risk, requires resources. Successful companies balance: monitor reactively nhưng act proactively "
            "khi có opportunities."
        ),
        "source": "Chapter 3, Responding to the Marketing Environment",
    },
    {
        "id": "Q34",
        "level": "medium",
        "question": "Tại sao post-recession consumers shift toward frugality affect marketing strategies như thế nào?",
        "ground_truth": (
            "Companies phải: (1) emphasize value over luxury, (2) adjust pricing strategies, "
            "(3) highlight durability/practicality, (4) avoid wasteful marketing, (5) develop budget-friendly options. "
            "Thậm chí luxury brands phải adapt messaging. Shift reflects permanent behavior change, không phải temporary."
        ),
        "source": "Chapter 3, The Changing Economic Environment",
    },
    {
        "id": "Q35",
        "level": "medium",
        "question": "Natural environment trends tạo opportunities và threats như thế nào cho marketers?",
        "ground_truth": (
            "Threats: resource shortages (raw materials scarce), pollution concerns (restrictions), climate change (disruptions). "
            "Opportunities: green products demand, sustainable practices as differentiator, eco-friendly innovations, "
            "corporate responsibility builds brand. Forward-thinking companies view as profit opportunity, không chỉ compliance."
        ),
        "source": "Chapter 3, The Natural Environment",
    },
    # ===========================================================================
    # CHAPTER 4: MARKETING INFORMATION (5 questions)
    # ===========================================================================
    {
        "id": "Q36",
        "level": "medium",
        "question": "Tại sao 'too much information can be as harmful as too little'?",
        "ground_truth": (
            "Quá nhiều data gây: (1) information overload - managers overwhelmed, (2) analysis paralysis - không decide được, "
            "(3) focus on wrong metrics, (4) waste time/resources collecting/storing irrelevant data. "
            "MIS phải balance between what users want vs what they need vs what's feasible."
        ),
        "source": "Chapter 4, Assessing Marketing Information Needs",
    },
    {
        "id": "Q37",
        "level": "medium",
        "question": "So sánh ưu nhược điểm của secondary data vs primary data",
        "ground_truth": (
            "Secondary: Ưu - quick, cheap, có insights không thể tự collect. Nhược - may không relevant, outdated, inaccurate, "
            "không fit exact needs. Primary: Ưu - specific to needs, current, controlled quality. Nhược - expensive, time-consuming, "
            "may lack expertise. Researchers usually start với secondary rồi mới collect primary."
        ),
        "source": "Chapter 4, Gathering Secondary Data and Primary Data Collection",
    },
    {
        "id": "Q38",
        "level": "medium",
        "question": "Phân biệt exploratory, descriptive, và causal research - khi nào dùng từng loại?",
        "ground_truth": (
            "Exploratory: gather preliminary info, define problems, suggest hypotheses - dùng khi unclear about problem. "
            "Descriptive: describe things (market potential, demographics) - dùng khi biết what to measure. "
            "Causal: test cause-effect relationships - dùng khi need prove relationships. "
            "Managers often start exploratory → descriptive/causal."
        ),
        "source": "Chapter 4, Defining the Problem and Research Objectives",
    },
    {
        "id": "Q39",
        "level": "medium",
        "question": "Tại sao observational research có thể reveal insights mà surveys không thể?",
        "ground_truth": (
            "Vì people often unwilling/unable to provide accurate answers about: (1) unconscious behaviors, "
            "(2) unexpressed needs/feelings, (3) socially undesirable actions, (4) things they've never thought about. "
            "Observation captures actual behavior, không phải reported behavior. However, cannot observe attitudes/motives."
        ),
        "source": "Chapter 4, Observational Research",
    },
    {
        "id": "Q40",
        "level": "medium",
        "question": "Big Data presents 'big opportunities and big challenges' - giải thích",
        "ground_truth": (
            "Opportunities: rich customer insights, real-time data, predict behavior, personalization. "
            "Challenges: overwhelming volume (information overload), difficult to analyze, privacy concerns, "
            "separating signal from noise. Companies need analytics capabilities và focus on 'right data' "
            "not just 'big data' để gain actionable insights."
        ),
        "source": "Chapter 4, Marketing Information and Today's Big Data",
    },
    # ===========================================================================
    # CHAPTER 5: CONSUMER BEHAVIOR (5 questions)
    # ===========================================================================
    {
        "id": "Q41",
        "level": "medium",
        "question": "Tại sao marketers không thể chỉ ask consumers what they need?",
        "ground_truth": (
            "Vì: (1) consumers themselves usually can't tell exactly what they need, (2) they don't understand why they buy, "
            "(3) unconscious motivations, (4) unexpressed feelings. Customer needs 'often anything but obvious.' "
            "Marketers phải use research, observation, analytics để uncover insights beyond what consumers say."
        ),
        "source": "Chapter 5, intro section",
    },
    {
        "id": "Q42",
        "level": "medium",
        "question": "Phân biệt membership groups vs reference groups trong ảnh hưởng social factors",
        "ground_truth": (
            "Membership groups: groups người directly belong to (family, work, clubs). "
            "Reference groups: serve as comparison/influence points nhưng may không belong to (aspirational groups, celebrities). "
            "Both influence buying through word-of-mouth, values, và norms. "
            "Reference groups powerful vì people aspire to be like them."
        ),
        "source": "Chapter 5, Social Factors",
    },
    {
        "id": "Q43",
        "level": "medium",
        "question": "Giải thích selective attention, selective distortion, và selective retention",
        "ground_truth": (
            "3 perceptual processes filter information: (1) Selective attention: people screen out most stimuli, "
            "notice những gì relate to needs. (2) Selective distortion: interpret info to fit existing beliefs. "
            "(3) Selective retention: remember points supporting attitudes, forget contradictory ones. "
            "Marketers phải work hard để grab attention và reinforce messages."
        ),
        "source": "Chapter 5, Psychological Factors - Perception",
    },
    {
        "id": "Q44",
        "level": "medium",
        "question": "So sánh complex buying behavior vs habitual buying behavior",
        "ground_truth": (
            "Complex: high involvement + significant brand differences (xe hơi) → extensive learning, evaluation. "
            "Habitual: low involvement + few differences (muối) → routine, brand familiarity, không có strong brand loyalty. "
            "Marketing strategies khác nhau: complex cần education/information; habitual cần repetition/visibility/price."
        ),
        "source": "Chapter 5, Types of Buying Decision Behavior",
    },
    {
        "id": "Q45",
        "level": "medium",
        "question": "Tại sao postpurchase cognitive dissonance quan trọng cho marketers?",
        "ground_truth": (
            "Dissonance là discomfort sau purchase, đặc biệt với expensive/important items. "
            "Quan trọng vì affect: (1) customer satisfaction, (2) repeat purchases, (3) word-of-mouth, (4) returns. "
            "Marketers must reinforce purchase decision qua communications, warranties, follow-ups để build confidence và loyalty."
        ),
        "source": "Chapter 5, The Buyer Decision Process - Postpurchase Behavior",
    },
    # ===========================================================================
    # CHAPTER 6: BUSINESS BUYER BEHAVIOR (5 questions)
    # ===========================================================================
    {
        "id": "Q46",
        "level": "medium",
        "question": "Tại sao business demand được gọi là 'derived demand'?",
        "ground_truth": (
            "Business demand derives from consumer demand cho final products. Ví dụ: demand for Gore-Tex fabric derives "
            "from consumer demand for outdoor clothing. Nếu consumer demand drops, business demand cũng drops. "
            "Marketers must understand both business customers và end consumers."
        ),
        "source": "Chapter 6, Market Structure and Demand",
    },
    {
        "id": "Q47",
        "level": "medium",
        "question": "So sánh straight rebuy, modified rebuy, và new task buying situations",
        "ground_truth": (
            "Straight rebuy: routine reorder, no changes, in-suppliers advantage. "
            "Modified rebuy: modify specs/prices/suppliers, opportunity for out-suppliers. "
            "New task: first-time purchase, greatest complexity, highest risk, most participants. "
            "Each requires different marketing approach và involvement level."
        ),
        "source": "Chapter 6, Major Types of Buying Situations",
    },
    {
        "id": "Q48",
        "level": "medium",
        "question": "Giải thích 5 roles trong buying center và tại sao marketers cần identify tất cả",
        "ground_truth": (
            "(1) Users: use product, (2) Influencers: affect decision (technical), (3) Buyers: make purchase, "
            "(4) Deciders: select suppliers, (5) Gatekeepers: control info flow. "
            "Marketers must identify all vì: each has different influence, concerns, criteria. "
            "Missing key participant có thể miss sale opportunity."
        ),
        "source": "Chapter 6, Participants in the Business Buying Process",
    },
    {
        "id": "Q49",
        "level": "medium",
        "question": "Tại sao e-procurement vừa có benefits vừa có drawbacks cho business relationships?",
        "ground_truth": (
            "Benefits: reduce costs, save time, increase efficiency, access wider suppliers. "
            "Drawbacks: may erode buyer-supplier relationships, less personal interaction, focus on price over value, "
            "reduce switching costs. Companies must balance efficiency gains với relationship maintenance."
        ),
        "source": "Chapter 6, E-procurement and Online Purchasing",
    },
    {
        "id": "Q50",
        "level": "medium",
        "question": "Systems selling (solutions selling) khác với product selling như thế nào?",
        "ground_truth": (
            "Product selling: bán individual products. Systems selling: provide complete, integrated solution to customer problem, "
            "often từ single seller. Benefits: convenience, compatibility, one-stop shopping. "
            "Requires deeper customer understanding, stronger relationships, và ability to coordinate multiple offerings."
        ),
        "source": "Chapter 6, Major Types of Buying Situations",
    },
    # ===========================================================================
    # LEVEL 3: CROSS-CHAPTER INTEGRATION (5 hard questions)
    # ===========================================================================
    {
        "id": "Q51",
        "level": "hard",
        "question": (
            "Một công ty có strong internal database và active social media monitoring. "
            "Tuy nhiên sales vẫn flat. Phân tích có thể có vấn đề gì trong marketing information system "
            "và đề xuất giải pháp."
        ),
        "ground_truth": (
            "Vấn đề có thể: (1) focus on data collection chứ không extract customer insights, "
            "(2) information không reach right decision makers at right time, (3) không translate insights thành action, "
            "(4) các departments không coordinate dùng insights. Giải pháp: establish customer insights teams, "
            "improve MIS distribution, integrate insights vào strategy process, train managers to use data-driven decisions, "
            "focus on actionable intelligence chứ không chỉ data volume."
        ),
        "source": "Integration of Chapter 4 (MIS framework, customer insights) + Chapter 2 (implementation, interdepartmental coordination)",
    },
    {
        "id": "Q52",
        "level": "hard",
        "question": (
            "Trong recession economy, làm thế nào một premium brand có thể maintain positioning "
            "mà vẫn address customer frugality mà không bị dilute brand?"
        ),
        "ground_truth": (
            "Strategies: (1) emphasize value proposition (quality/durability = long-term savings), "
            "(2) tiered offerings (keep premium line, add accessible tier riêng brand), "
            "(3) highlight 'affordable luxury' aspects, (4) payment plans/financing, "
            "(5) focus on emotional benefits không chỉ price. Key là adjust messaging/tactics nhưng protect core brand identity "
            "và avoid direct price competition. Maintain customer-perceived value cao hơn costs."
        ),
        "source": "Integration of Chapter 3 (economic environment) + Chapter 1 (customer value/satisfaction, positioning) + Chapter 5 (perception)",
    },
    {
        "id": "Q53",
        "level": "hard",
        "question": (
            "Một B2B company muốn transition từ product-focused sang solution-focused selling. "
            "Những thay đổi gì cần có trong: marketing research approach, sales process, "
            "và customer relationship management?"
        ),
        "ground_truth": (
            "Research: shift from product specs research sang understanding customer business problems, value analysis, "
            "total cost of ownership. Need deeper ethnographic/qualitative methods. "
            "Sales: từ transactional sang consultative, longer cycle, involve more participants, focus ROI. "
            "CRM: track broader relationship metrics (not just sales), manage multiple touchpoints, coordinate cross-functional teams, "
            "measure customer success outcomes. Overall: từ selling products sang solving problems."
        ),
        "source": "Integration of Chapter 6 (systems selling, buying process) + Chapter 4 (research approaches) + Chapter 2 (value chain) + CRM concepts",
    },
    {
        "id": "Q54",
        "level": "hard",
        "question": (
            "Giải thích tại sao understanding buyer decision process quan trọng hơn chỉ understanding demographics "
            "khi design marketing strategy. Sử dụng ví dụ để minh họa."
        ),
        "ground_truth": (
            "Demographics chỉ cho biết WHO (age, income, location) nhưng không explain WHY và HOW people buy. "
            "Decision process reveals: (1) information sources used → where to promote, (2) evaluation criteria → what benefits to emphasize, "
            "(3) influencers → who to target, (4) postpurchase behavior → how to build loyalty. "
            "Ví dụ: 2 người cùng demographic có thể có completely different decision processes (complex vs habitual). "
            "Effective marketing requires understanding BOTH who và how they buy, rồi integrate vào comprehensive strategy addressing mỗi stage."
        ),
        "source": "Integration of Chapter 5 (buyer decision process, buyer characteristics) + Chapter 2 (marketing strategy) + Chapter 1 (segmentation)",
    },
    {
        "id": "Q55",
        "level": "hard",
        "question": (
            "Phân tích mối quan hệ giữa mission statement, business portfolio decisions, marketing environment analysis, "
            "và marketing information system. Chúng interact với nhau như thế nào trong strategic planning process?"
        ),
        "ground_truth": (
            "Chúng form integrated system: (1) Mission statement defines purpose/direction → guides portfolio decisions. "
            "(2) Environment analysis identifies opportunities/threats trong macro/micro forces → influences what businesses to invest/divest. "
            "(3) MIS provides data về customers, competitors, trends → supports environment analysis và portfolio evaluation. "
            "(4) Portfolio decisions allocate resources based on mission + environment + data insights. "
            "Flow: Mission → Environment scan (using MIS) → Portfolio analysis → Strategy. Continuous cycle: MIS feeds environment analysis, "
            "environment shapes portfolio, portfolio aligns with mission. Không thể make effective decisions without integrating all components."
        ),
        "source": "Integration of Chapter 2 (strategic planning framework, mission, portfolio) + Chapter 3 (environment analysis) + Chapter 4 (MIS role)",
    },
]


def get_extended_questions_by_level(level: str) -> list:
    """Get extended questions filtered by difficulty level."""
    return [q for q in EXTENDED_TEST_QUESTIONS if q["level"] == level]


def get_all_extended_questions() -> list:
    """Get all extended test questions."""
    return EXTENDED_TEST_QUESTIONS


if __name__ == "__main__":
    print(f"Total extended questions: {len(EXTENDED_TEST_QUESTIONS)}")
    print(f"  Medium: {len(get_extended_questions_by_level('medium'))}")
    print(f"  Hard: {len(get_extended_questions_by_level('hard'))}")
