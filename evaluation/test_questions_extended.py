"""
Extended Marketing Knowledge Test Questions

125 additional questions focusing on logical thinking and marketing principles,
NOT specific case studies. Questions test conceptual understanding and application.

Coverage:
- Q21-Q55: Chapters 1-6 foundations (35 questions)
- Q56-Q95: Chapters 7-11 + parts of 4-5 (40 questions from generating_test_3.md)
- Q96-Q145: Chapters 12-20 (50 questions from generating_test_4.md)

Source: Principles of Marketing 17th Edition - Kotler & Armstrong
Generated from: docs/evaluation/generating_tests_2.md, generating_test_3.md, generating_test_4.md
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
    # ===========================================================================
    # CHAPTER 7: CUSTOMER-DRIVEN MARKETING STRATEGY (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q56",
        "level": "medium",
        "question": "Một công ty đang phân vân giữa undifferentiated marketing và differentiated marketing. Những yếu tố nào nên cân nhắc để quyết định?",
        "ground_truth": (
            "Cần xem xét: (1) Company resources - limited resources → undifferentiated, "
            "(2) Product variability - uniform products (muối) → undifferentiated; variable products (xe) → differentiated, "
            "(3) Product life cycle stage - new product → undifferentiated; mature → differentiated, "
            "(4) Market variability - customers giống nhau → undifferentiated, "
            "(5) Competitors' strategies - avoid làm giống competitors. Trade-off: increased sales vs increased costs."
        ),
        "source": "Chapter 7, Choosing a Targeting Strategy",
    },
    {
        "id": "Q57",
        "level": "medium",
        "question": "Tại sao các công ty có thể profitable khi focus vào niche markets mặc dù market size nhỏ hơn mass market?",
        "ground_truth": (
            "Concentrated marketing profitable vì: (1) strong market position do greater knowledge về niche needs, "
            "(2) special reputation trong niche, (3) marketing more effectively - fine-tune products/prices/programs, "
            "(4) marketing more efficiently - target chỉ best customers, (5) less competition trong overlooked niches, "
            "(6) higher customer loyalty. Small companies thường start as nichers trước khi grow broader."
        ),
        "source": "Chapter 7, Concentrated Marketing",
    },
    {
        "id": "Q58",
        "level": "medium",
        "question": "Phân biệt benefit segmentation với demographic segmentation. Khi nào nên ưu tiên benefit segmentation?",
        "ground_truth": (
            "Demographic: chia theo age, income, gender - dễ measure và reach. "
            "Benefit: chia theo benefits sought - powerful hơn vì directly relate to customer needs. "
            "Nên ưu tiên benefits khi: (1) demographics không predict behavior tốt, (2) same demographic có very different needs, "
            "(3) product functionality là key differentiation. Nhiều marketers believe behavior variables là best starting point."
        ),
        "source": "Chapter 7, Behavioral Segmentation - Benefits Sought",
    },
    {
        "id": "Q59",
        "level": "medium",
        "question": "Requirements for effective segmentation gồm những gì? Tại sao không phải mọi cách segment đều effective?",
        "ground_truth": (
            "5 requirements: (1) Measurable - có thể đo size/power/profiles, (2) Accessible - reach và serve được, "
            "(3) Substantial - đủ lớn/profitable, (4) Differentiable - respond khác nhau với marketing mix, "
            "(5) Actionable - design effective programs được. Segment như 'blonde vs brunette salt buyers' không effective "
            "vì hair color không affect purchase và không meet các criteria trên."
        ),
        "source": "Chapter 7, Requirements for Effective Segmentation",
    },
    {
        "id": "Q60",
        "level": "medium",
        "question": "Giải thích mối quan hệ giữa positioning và value proposition. Cho ví dụ minh họa.",
        "ground_truth": (
            "Positioning là how product is perceived in consumers' minds vs competitors. "
            "Value proposition là full mix of benefits brand offers to deliver vị trí đó. "
            "Relationship: positioning statement → guides value proposition → delivered qua marketing mix. "
            "Ví dụ: IKEA positioned as 'Life improvement store' → value proposition là affordable, functional home furnishings + in-store experience + self-assembly."
        ),
        "source": "Chapter 7, Differentiation and Positioning",
    },
    # ===========================================================================
    # CHAPTER 8: PRODUCTS, SERVICES, AND BRANDS (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q61",
        "level": "medium",
        "question": "Phân tích 3 levels of product và giải thích tại sao marketers phải think beyond actual product",
        "ground_truth": (
            "(1) Core customer value - benefit thực sự buyer seeks (lipstick = hope không chỉ lip color), "
            "(2) Actual product - features, design, quality, brand, packaging, "
            "(3) Augmented product - additional services (warranty, support, delivery). "
            "Marketers must think beyond actual vì: customers buy bundles of benefits, không chỉ physical attributes. "
            "Augmentation creates differentiation và customer loyalty."
        ),
        "source": "Chapter 8, Levels of Product and Services",
    },
    {
        "id": "Q62",
        "level": "medium",
        "question": "So sánh convenience, shopping, specialty, và unsought products về customer buying behavior và marketing implications",
        "ground_truth": (
            "Convenience: frequent purchase, minimal effort → low price, mass promotion, widespread distribution. "
            "Shopping: careful comparison → higher price, selective distribution, advertising + personal selling. "
            "Specialty: unique, willing special effort → high price, exclusive distribution, targeted promotion. "
            "Unsought: not aware/consider → varies price, aggressive selling required. Each type demands completely different marketing approach."
        ),
        "source": "Chapter 8, Product and Service Classifications",
    },
    {
        "id": "Q63",
        "level": "medium",
        "question": "Tại sao service intangibility tạo ra marketing challenges? Làm thế nào service providers có thể overcome?",
        "ground_truth": (
            "Challenges: Customers không thể see/taste/feel trước khi buy → uncertainty, khó judge quality. "
            "Solutions: (1) make service tangible qua physical evidence (facilities, people, equipment), "
            "(2) use signals of quality (price, certifications), (3) leverage customer testimonials, (4) strong branding, "
            "(5) social media để show experiences của others. Ví dụ Mayo Clinic uses facilities, social media, patient stories."
        ),
        "source": "Chapter 8, Service Intangibility",
    },
    {
        "id": "Q64",
        "level": "medium",
        "question": "Giải thích Service Profit Chain và tại sao employee satisfaction quan trọng cho service businesses",
        "ground_truth": (
            "5 links: (1) Internal service quality → (2) Satisfied employees → (3) Greater service value → "
            "(4) Satisfied loyal customers → (5) Healthy service profits. "
            "Employee satisfaction critical vì: services inseparable from providers, employees co-create service với customers. "
            "Unhappy employees → poor service → dissatisfied customers → lost profits. Investment in employees actually investment in customer satisfaction."
        ),
        "source": "Chapter 8, The Service Profit Chain",
    },
    {
        "id": "Q65",
        "level": "medium",
        "question": "Line stretching vs line filling - khi nào dùng mỗi strategy và potential risks?",
        "ground_truth": (
            "Line stretching: lengthen beyond current range (upward/downward/both). Dùng khi: plug market holes, respond competitors, capture growth segments. Risk: dilute positioning. "
            "Line filling: add items within range. Dùng khi: extra profits, satisfy dealers, keep out competitors. Risk: cannibalization và customer confusion. "
            "Cần ensure new items noticeably different và align với brand positioning."
        ),
        "source": "Chapter 8, Product Line Decisions",
    },
    # ===========================================================================
    # CHAPTER 9: NEW PRODUCT DEVELOPMENT & PLC (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q66",
        "level": "medium",
        "question": "Tại sao new products có high failure rate? Làm thế nào companies có thể reduce failure risks?",
        "ground_truth": (
            "Failure reasons: (1) overestimate market size, (2) poorly designed product, (3) incorrect positioning, "
            "(4) wrong timing/pricing, (5) poor advertising, (6) competitors fight back, (7) higher costs than expected. "
            "Reduce risks: systematic development process, customer-centered approach, thorough testing, understand consumers/markets/competitors, create superior value, validate concepts early."
        ),
        "source": "Chapter 9, New Product Development Strategy",
    },
    {
        "id": "Q67",
        "level": "medium",
        "question": "So sánh internal vs external sources cho idea generation. Ưu nhược điểm của mỗi nguồn?",
        "ground_truth": (
            "Internal (R&D, employees): Ưu - align với capabilities, protect IP, fast execution. Nhược - limited perspectives, groupthink. "
            "External (customers, competitors, suppliers, crowdsourcing): Ưu - diverse ideas, customer validation, unexpected innovations. "
            "Nhược - hard to evaluate volume, IP risks, may không fit capabilities. Best approach: extensive innovation networks tận dụng cả hai."
        ),
        "source": "Chapter 9, Idea Generation",
    },
    {
        "id": "Q68",
        "level": "medium",
        "question": "Phân biệt concept testing với test marketing. Mục đích và timing của mỗi stage?",
        "ground_truth": (
            "Concept testing: early stage, test concept với target consumers qua descriptions/images, assess appeal trước khi develop physical product, low cost. "
            "Test marketing: later stage, test actual product + marketing program trong realistic settings, gain experience trước full launch, expensive. "
            "Companies may skip test marketing nếu low risk hoặc fast-changing markets require speed."
        ),
        "source": "Chapter 9, Concept Development and Testing, Test Marketing",
    },
    {
        "id": "Q69",
        "level": "medium",
        "question": "Team-based development vs sequential development - trade-offs và khi nào nên dùng team-based?",
        "ground_truth": (
            "Sequential: từng department works riêng, orderly, controlled nhưng slow. "
            "Team-based: cross-functional teams overlap steps, faster, more effective nhưng có organizational tension. "
            "Nên dùng team-based khi: (1) fast-changing markets, (2) short product life cycles, (3) need speed to market, (4) complex products need coordination. "
            "Rewards of speed > risks of tension."
        ),
        "source": "Chapter 9, Team-Based New Product Development",
    },
    {
        "id": "Q70",
        "level": "medium",
        "question": "Trong maturity stage, marketer có 3 options: modify market, product, hoặc marketing mix. Khi nào nên chọn mỗi option?",
        "ground_truth": (
            "Modify market: find new users/segments/usage - khi có untapped segments. "
            "Modify product: change quality/features/style - khi product aging hoặc new tech available. "
            "Modify marketing mix: change price/promotion/distribution - khi positioning needs refresh nhưng product still relevant. "
            "Thường combine cả 3. Good offense là best defense - don't just defend, proactively evolve product."
        ),
        "source": "Chapter 9, Maturity Stage",
    },
    # ===========================================================================
    # CHAPTER 10: PRICING FUNDAMENTALS (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q71",
        "level": "medium",
        "question": "Tại sao value-based pricing 'superior' hơn cost-based pricing? Nhưng tại sao nhiều companies vẫn dùng cost-based?",
        "ground_truth": (
            "Value-based superior vì: starts với customer perceptions, aligns price với value delivered, maximizes customer satisfaction và willingness to pay. "
            "Cost-based vẫn popular vì: (1) easier - costs measurable hơn demand, (2) less frequent adjustments needed, "
            "(3) fair to both parties, (4) when all use it → price stability. However, ignoring demand và competitors = suboptimal pricing."
        ),
        "source": "Chapter 10, Customer Value–Based Pricing vs Cost-Based Pricing",
    },
    {
        "id": "Q72",
        "level": "medium",
        "question": "Giải thích experience curve và risks của experience-curve pricing strategy",
        "ground_truth": (
            "Experience curve: average cost decreases với accumulated production experience do learning, efficiencies, economies of scale. "
            "Strategy: price low → high volume → lower costs → lower prices further. "
            "Risks: (1) cheap image, (2) assumes weak competitors won't fight, (3) new technology may disrupt, (4) focus quá nhiều on cost chứ không innovation/value. Không always work."
        ),
        "source": "Chapter 10, Costs as a Function of Production Experience",
    },
    {
        "id": "Q73",
        "level": "medium",
        "question": "Target costing khác với cost-plus pricing như thế nào? Khi nào nên dùng target costing?",
        "ground_truth": (
            "Cost-plus: design product → calculate cost → add markup → price. "
            "Target costing: determine ideal price (from customer value) → target costs to meet price → design product. "
            "Nên dùng target costing khi: (1) competitive markets với price sensitivity, (2) clear customer value perceptions, "
            "(3) flexible manufacturing capabilities, (4) can design to cost. Ví dụ: Honda Fit designed to $13,950 price point."
        ),
        "source": "Chapter 10, Overall Marketing Strategy, Objectives, and Mix",
    },
    {
        "id": "Q74",
        "level": "medium",
        "question": "Price elasticity affect pricing decisions như thế nào? Cho examples của elastic vs inelastic demand",
        "ground_truth": (
            "Elastic demand: price change → large demand change. Strategy: lower price → increase revenue. Examples: luxury goods, có substitutes. "
            "Inelastic demand: price change → small demand change. Strategy: có thể raise price without losing volume. Examples: necessities, no substitutes, urgent needs. "
            "Marketers must understand elasticity để optimize revenue không chỉ volume."
        ),
        "source": "Chapter 10, The Market and Demand",
    },
    {
        "id": "Q75",
        "level": "medium",
        "question": "Tại sao 'more-for-more' positioning có thể fail? Điều kiện nào cần thiết để thành công?",
        "ground_truth": (
            "Can fail nếu: (1) customers không perceive sufficient value difference, (2) economic downturn reduces willingness to pay premium, "
            "(3) competitors offer 'more-for-same', (4) fake/exaggerated superiority. "
            "Success conditions: (1) truly superior quality/features, (2) target segment values và can afford, (3) consistent delivery of promise, "
            "(4) strong brand building, (5) protect differentiation. Ví dụ LEGO succeed với quality focus."
        ),
        "source": "Chapter 10 + Chapter 7 value propositions",
    },
    # ===========================================================================
    # CHAPTER 11: PRICING STRATEGIES (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q76",
        "level": "medium",
        "question": "So sánh market-skimming pricing với market-penetration pricing. Khi nào nên chọn mỗi strategy?",
        "ground_truth": (
            "Skimming: high initial price, skim revenue từng layers. Dùng khi: (1) high-quality innovative product, (2) enough buyers willing pay high, "
            "(3) costs small volume not too high, (4) high price doesn't attract competitors. "
            "Penetration: low price attract large buyers, gain share. Dùng khi: (1) price-sensitive market, (2) costs decrease với volume, "
            "(3) low price deters competition, (4) mass market potential."
        ),
        "source": "Chapter 11, Market-Skimming Pricing và Market-Penetration Pricing",
    },
    {
        "id": "Q77",
        "level": "medium",
        "question": "Captive-product pricing strategy có advantages gì nhưng cũng có risks gì? Làm sao balance?",
        "ground_truth": (
            "Strategy: price main product low, captive products high (razors-blades, printers-ink, Kindle-ebooks). "
            "Advantages: attract customers với low entry, profit from ongoing purchases. "
            "Risks: customer resentment nếu captive price quá cao, switch to competitors' captives, negative word-of-mouth. "
            "Balance: reasonable markup trên captives, communicate value, không exploit customers."
        ),
        "source": "Chapter 11, Captive-Product Pricing",
    },
    {
        "id": "Q78",
        "level": "medium",
        "question": "Tại sao psychological pricing effective? Mechanisms nào make it work?",
        "ground_truth": (
            "Mechanisms: (1) Price as quality signal - consumers use price to infer quality khi lack info, "
            "(2) Reference prices - consumers compare vs mental benchmarks, (3) Price endings - $.99 signals bargain, whole numbers signal quality, "
            "(4) Price-quality association. Effective vì leverages consumer psychology và perceptions, không chỉ rational calculation. "
            "Small price differences có thể significantly impact perception."
        ),
        "source": "Chapter 11, Psychological Pricing",
    },
    {
        "id": "Q79",
        "level": "medium",
        "question": "Promotional pricing có short-term benefits nhưng long-term dangers gì? Khi nào should avoid?",
        "ground_truth": (
            "Benefits: boost short-term sales, create urgency, clear inventory, attract deal-prone customers. "
            "Dangers: (1) brand erosion - giảm perceived value, (2) create deal-prone customers - chỉ buy on sale, (3) reduced margins, "
            "(4) competitors match → price war. Avoid khi: premium brand positioning, strong brand equity to protect, market leader, customers value quality over deals."
        ),
        "source": "Chapter 11, Promotional Pricing",
    },
    {
        "id": "Q80",
        "level": "medium",
        "question": "Dynamic pricing có advantages gì cho both sellers và buyers? Nhưng ethical concerns là gì?",
        "ground_truth": (
            "Seller advantages: optimize revenue, match supply-demand, personalization. "
            "Buyer advantages: access to price comparisons, deals for flexible shoppers, price transparency. "
            "Ethical concerns: (1) fairness - same product, different prices, (2) exploitation of urgency, (3) discrimination, "
            "(4) customer resentment nếu discover differences. Legal if không discriminate nhưng must balance profit với customer trust."
        ),
        "source": "Chapter 11, Dynamic and Online Pricing",
    },
    # ===========================================================================
    # CHAPTER 4: MARKETING INFORMATION REVISITED (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q81",
        "level": "medium",
        "question": "Phân biệt competitive marketing intelligence với marketing research về purpose và methods",
        "ground_truth": (
            "Intelligence: broad environmental scanning, ongoing monitoring của consumers/competitors/developments, publicly available info. "
            "Research: focused studies cho specific decisions, systematic design/collection/analysis, may involve primary data. "
            "Intelligence identifies opportunities/threats; research provides detailed answers to specific questions. "
            "Cần cả hai: intelligence cho big picture, research cho tactical decisions."
        ),
        "source": "Chapter 4, Competitive Marketing Intelligence vs Marketing Research",
    },
    {
        "id": "Q82",
        "level": "medium",
        "question": "Tại sao customer insights teams quan trọng hơn traditional data providers? Họ làm gì khác?",
        "ground_truth": (
            "Traditional data providers: just collect và distribute data. "
            "Insights teams: (1) extract actionable insights từ data, (2) temper data với judgment, (3) work strategically với decision makers, "
            "(4) drive business decisions, (5) share insights engagingly. Transform from 'what happened' → 'what it means' → 'what to do'. "
            "Value không ở data mà ở insights."
        ),
        "source": "Chapter 4, Managing Marketing Information",
    },
    {
        "id": "Q83",
        "level": "medium",
        "question": "Behavioral targeting và social targeting khác nhau như thế nào? Privacy implications?",
        "ground_truth": (
            "Behavioral: track consumer movements across sites, target ads based on browsing history. "
            "Social: mine social connections/conversations, target based on friends' behaviors. Social powerful hơn vì consumers shop like friends. "
            "Privacy issues: fine line between 'serving' và 'stalking', customers feel profiled, concerns về data misuse. "
            "Need transparency và respect boundaries."
        ),
        "source": "Chapter 4, Online Behavioral and Social Tracking",
    },
    {
        "id": "Q84",
        "level": "medium",
        "question": "CRM software alone không đủ để build customer relationships. Cần gì ngoài technology?",
        "ground_truth": (
            "Technology chỉ là tool. Cần: (1) start với fundamentals of managing relationships, (2) focus on 'R' (relationship) không chỉ technology, "
            "(3) customer-centric culture, (4) trained employees to use insights, (5) integration across departments, (6) actionable strategies từ data. "
            "Common mistake: view CRM as technology process only hoặc buried in data details mà miss big picture."
        ),
        "source": "Chapter 4, Customer Relationship Management (CRM)",
    },
    {
        "id": "Q85",
        "level": "medium",
        "question": "Probability sampling vs nonprobability sampling - trade-offs và khi nào accept nonprobability?",
        "ground_truth": (
            "Probability: mỗi member có known chance, can calculate confidence limits, accurate, representative. "
            "Nonprobability: không known chance, cannot measure error, less accurate. "
            "Accept nonprobability khi: (1) probability costs too much, (2) takes too much time, (3) exploratory research, (4) quick insights needed. "
            "Trade-off: cost/speed vs statistical accuracy."
        ),
        "source": "Chapter 4, Sampling Plan",
    },
    # ===========================================================================
    # CHAPTER 5: CONSUMER BEHAVIOR REVISITED (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q86",
        "level": "medium",
        "question": "Tại sao culture là 'most basic cause' của wants và behavior? Làm thế nào cultural shifts create opportunities?",
        "ground_truth": (
            "Culture shape basic values, perceptions, wants, behaviors learned from childhood. 'Most basic' vì: deeply rooted, broad influence, affect fundamental needs expression. "
            "Cultural shifts create opportunities: health/fitness shift → health industry boom, environmental concern → green products, digital lifestyle → tech products. "
            "Marketers must spot shifts early để capitalize."
        ),
        "source": "Chapter 5, Cultural Factors",
    },
    {
        "id": "Q87",
        "level": "medium",
        "question": "Word-of-mouth influence và opinion leaders powerful như thế nào? Marketers leverage làm sao?",
        "ground_truth": (
            "Powerful vì: (1) trusted source - people trust friends hơn ads, (2) relevant - friends có similar needs, (3) social proof, (4) amplified qua social networks. "
            "Leverage: (1) identify opinion leaders, (2) create shareable experiences, (3) encourage advocacy, (4) influencer partnerships, "
            "(5) make customers brand partners. Ví dụ: Mountain Dew's Dew Nation, loyalty customers promote brand."
        ),
        "source": "Chapter 5, Social Factors",
    },
    {
        "id": "Q88",
        "level": "medium",
        "question": "Lifestyle segmentation powerful hơn demographics vì sao? Nhưng challenges trong implementation?",
        "ground_truth": (
            "Powerful vì: people in same demographic có very different lifestyles → different needs/purchases. "
            "Lifestyle (activities, interests, opinions) directly relates to buying behavior. "
            "Challenges: (1) harder to measure than demographics, (2) harder to reach - không clear media/channels, "
            "(3) lifestyle changes over time, (4) expensive research. Must often combine với demographics để actionable."
        ),
        "source": "Chapter 7, Psychographic Segmentation",
    },
    {
        "id": "Q89",
        "level": "medium",
        "question": "Variety-seeking behavior vs brand loyalty - implications cho marketing strategies?",
        "ground_truth": (
            "Variety-seeking: low involvement, switch for novelty, try different brands. Strategy: (1) dominant shelf space/visibility, "
            "(2) lower prices/deals, (3) variety in own line, (4) encourage trial. "
            "Loyalty: repeat same brand. Strategy: (1) maintain quality consistency, (2) reinforce satisfaction, "
            "(3) loyalty programs, (4) engage deeply, (5) make partners. Completely different approaches."
        ),
        "source": "Chapter 5, Types of Buying Decision Behavior + Loyalty Status",
    },
    {
        "id": "Q90",
        "level": "medium",
        "question": "Cognitive dissonance sau purchase ảnh hưởng đến customer relationships như thế nào? Prevention strategies?",
        "ground_truth": (
            "Dissonance → buyer doubt → (1) decreased satisfaction, (2) negative word-of-mouth, (3) returns, (4) lost repeat business, (5) weakened relationships. "
            "Prevention: (1) realistic expectations upfront, (2) post-purchase communications reassuring decision, "
            "(3) warranties/guarantees, (4) follow-up support, (5) make easy to contact với concerns. Goal: reinforce purchase decision confidence."
        ),
        "source": "Chapter 5, Postpurchase Behavior + Chapter 1 Customer Satisfaction concepts",
    },
    # ===========================================================================
    # CROSS-CHAPTER LEVEL 3: HARD QUESTIONS (5 questions from generating_test_3.md)
    # ===========================================================================
    {
        "id": "Q91",
        "level": "hard",
        "question": (
            "Một công ty đang trong maturity stage muốn revitalize brand. Analyze làm thế nào họ phải integrate: "
            "product life cycle management, repositioning strategy, market research, và customer insights để successful turnaround."
        ),
        "ground_truth": (
            "Integrated approach: (1) Research customers (Ch.4) - understand why brand aging, changing needs, competitive threats. "
            "Use both quantitative và qualitative để deep insights. (2) Analyze environment (Ch.3) - demographic shifts, cultural trends, technology changes. "
            "(3) Redefine positioning (Ch.7) - based on insights, identify new target segments hoặc new value proposition. "
            "(4) Product decisions (Ch.8-9) - modify product features, packaging, augmented services to match new positioning. "
            "(5) PLC strategy (Ch.9) - use market modification (new users), product modification (modernize), marketing mix modification (new channels/messages). "
            "Critical success factors: customer-centered throughout, systematic process, don't abandon core strengths mà leverage them differently, test concepts before full relaunch."
        ),
        "source": "Integration of Chapters 4 (research), 7 (positioning), 8 (product decisions), 9 (PLC maturity stage)",
    },
    {
        "id": "Q92",
        "level": "hard",
        "question": (
            "Explain cách một startup với limited resources có thể compete effectively against established players. "
            "Integrate concepts về targeting strategy, positioning, pricing, và new product development."
        ),
        "ground_truth": (
            "Systematic approach: (1) Niche targeting (Ch.7) - concentrated marketing vào overlooked segment thay vì compete broadly. "
            "Leverage: greater knowledge, special reputation, efficient marketing. "
            "(2) Clear differentiation (Ch.7) - identify benefit mà big players ignore hoặc can't deliver. Position on unique value. "
            "(3) Smart product development (Ch.9) - customer-centered, crowdsource ideas, lean development, fail fast. Validate concepts early, avoid expensive mistakes. "
            "(4) Value-based pricing (Ch.10) - don't compete on price với large players (they win). Price on value differentiation. Có thể premium if justify value. "
            "(5) Digital leverage (Ch.1, 4) - use digital marketing cost-effectively, build community, engage customers directly. "
            "Success = focus + differentiation + value delivery."
        ),
        "source": "Integration of Ch.7 concentrated marketing, Ch.9 systematic development, Ch.10 value pricing",
    },
    {
        "id": "Q93",
        "level": "hard",
        "question": (
            "Một B2B company transition từ selling products sang selling solutions/systems. "
            "Những fundamental changes cần có across: buyer understanding, value proposition, pricing approach, và relationship management?"
        ),
        "ground_truth": (
            "Transformation requires: (1) Buyer understanding (Ch.6) - shift from understanding product specs → understanding customer's business problems, "
            "total cost of ownership, ROI. Involve multiple buying center members (users, influencers, deciders). Longer decision process. "
            "(2) Value proposition (Ch.7, 8) - from product features → business outcomes solved. Augmented product crucial - services, support, customization. "
            "(3) Pricing (Ch.10-11) - from cost-plus → value-based pricing on total solution value. Consider product bundle pricing. Focus on customer value created không chỉ costs. "
            "(4) Relationships (Ch.1, 6) - from transactional → consultative partnerships. Supplier development, co-creation, performance review based on customer success. "
            "Key mindset shift: selling solutions to customer problems, not products to buyers."
        ),
        "source": "Integration of Ch.6 systems selling, Ch.8 augmented product, Ch.10 value-based pricing, Ch.4 research approaches",
    },
    {
        "id": "Q94",
        "level": "hard",
        "question": (
            "Analyze trade-offs giữa mass customization/individual marketing với operational efficiency và profitability. "
            "Khi nào benefits outweigh costs?"
        ),
        "ground_truth": (
            "Trade-offs: Benefits (Ch.7) - perfect fit customer needs, premium prices, customer delight, loyalty, word-of-mouth. "
            "Costs - (1) higher production costs (Ch.10) - lose economies of scale, complex operations, "
            "(2) logistical complexity - inventory, delivery, (3) marketing costs - personalized communications. "
            "Benefits outweigh when: (1) customers willing pay premium for customization, (2) technology enables cost-effective customization (digital, robotics), "
            "(3) high customer lifetime value justifies acquisition costs, (4) differentiation critical trong competitive market, "
            "(5) customization data provides insights for improvements. "
            "New technologies (Ch.3, 9) - digital/flexible manufacturing make feasible. Examples: Nike ID, Rolls-Royce Bespoke profitable vì right customers, right execution."
        ),
        "source": "Integration of Ch.7 individual marketing, Ch.10 cost considerations, Ch.8 customization examples",
    },
    {
        "id": "Q95",
        "level": "hard",
        "question": (
            "Một premium brand facing economic recession. Design comprehensive strategy addressing: value perception, pricing tactics, "
            "product portfolio, target segments, và brand equity protection. Không được sacrifice long-term positioning."
        ),
        "ground_truth": (
            "Holistic recession strategy: (1) Reframe value (Ch.10) - emphasize quality = long-term savings, durability, investment value. "
            "Good-value pricing for entry options nhưng maintain premium core. "
            "(2) Portfolio approach (Ch.2, 8) - introduce accessible tier (Mercedes CLA) hoặc value sub-brand (riêng identity), keep flagship premium. Line stretching downward but differentiate clearly. "
            "(3) Segment strategy (Ch.7) - maintain loyal affluent customers, simultaneously attract 'affordable luxury' aspirants. Different products/messages for each. "
            "(4) Product augmentation (Ch.8) - enhance services, warranties, financing to add value without cutting price. "
            "(5) Communication (Ch.1) - focus messaging on value proposition không chỉ price. Highlight emotional benefits, craftsmanship, heritage. "
            "(6) Pricing tactics (Ch.11) - payment plans, trade-in allowances, seasonal promotions (limited) nhưng avoid habitual discounting. "
            "Critical balance: offer options for tough times nhưng protect core brand equity và premium associations long-term."
        ),
        "source": "Integration of Ch.3 economic environment, Ch.10 good-value pricing, Ch.8 product lines, Ch.7 segmentation/positioning",
    },
    # ===========================================================================
    # CHAPTER 12: MARKETING CHANNELS (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q96",
        "level": "medium",
        "question": "Tại sao producers sử dụng intermediaries thay vì bán trực tiếp? Trade-offs là gì?",
        "ground_truth": (
            "Benefits intermediaries: (1) greater efficiency - reduce contacts needed, (2) economies from contacts/experience/specialization/scale, "
            "(3) transform assortments (producers make narrow/large, consumers want broad/small), (4) bridge time/place/possession gaps. "
            "Trade-offs: give up control over how/to whom sell, share margins. Must assign functions to members that add most value for cost."
        ),
        "source": "Chapter 12, How Channel Members Add Value",
    },
    {
        "id": "Q97",
        "level": "medium",
        "question": "So sánh vertical marketing systems (VMS) với conventional distribution channels",
        "ground_truth": (
            "Conventional: independent firms, mỗi maximize own profits (có thể at expense of system), no leadership/control, damaging conflict. "
            "VMS: unified system, one member owns/contracts/dominates others, coordinated activities, managed conflict, better performance. "
            "3 types VMS: corporate (ownership), contractual (contracts/franchises), administered (power). VMS emerged để overcome conventional channel weaknesses."
        ),
        "source": "Chapter 12, Vertical Marketing Systems",
    },
    {
        "id": "Q98",
        "level": "medium",
        "question": "Disintermediation tạo opportunities và threats như thế nào? Examples?",
        "ground_truth": (
            "Definition: cutting out intermediaries - producers go direct HOẶC new intermediaries displace traditional. "
            "Opportunities: innovators can disrupt, reap rewards (Netflix streaming displaced DVD rental). "
            "Threats: traditional intermediaries swept aside (music stores → iTunes → streaming services). "
            "Must continue innovate để survive. Implications: both producers và resellers phải adapt hoặc become obsolete."
        ),
        "source": "Chapter 12, Changing Channel Organization - Disintermediation",
    },
    {
        "id": "Q99",
        "level": "medium",
        "question": "Channel design phải start với analyzing consumer needs. Tại sao? Những needs nào cần consider?",
        "ground_truth": (
            "Vì channels are part of customer value delivery network - must serve customer preferences. "
            "Consumer needs: (1) location - nearby vs travel?, (2) buying method - in person/phone/online?, (3) assortment - breadth vs specialization?, "
            "(4) add-on services - delivery/installation/repairs?, (5) speed. Must balance desired service levels với feasibility, costs, và customer price sensitivity."
        ),
        "source": "Chapter 12, Analyzing Consumer Needs",
    },
    {
        "id": "Q100",
        "level": "medium",
        "question": "Phân biệt intensive, selective, và exclusive distribution. Khi nào dùng mỗi strategy?",
        "ground_truth": (
            "Intensive: stock in as many outlets as possible - dùng cho convenience products (toothpaste, candy) cần maximum exposure. "
            "Selective: more than one but fewer than all - consumer electronics, furniture cần better relationships/service. "
            "Exclusive: limited dealers only - luxury brands (Breitling watches) enhance positioning, stronger dealer support. "
            "Trade-off: market coverage vs control vs brand image."
        ),
        "source": "Chapter 12, Number of Marketing Intermediaries",
    },
    # ===========================================================================
    # CHAPTER 13: RETAILING AND WHOLESALING (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q101",
        "level": "medium",
        "question": "Shopper marketing và 'zero moment of truth' thay đổi retail strategy như thế nào?",
        "ground_truth": (
            "Traditional: 'first moment of truth' = 3-7 seconds at shelf in store. "
            "Now: 'zero moment of truth' = consumers research online BEFORE visiting store. Omni-channel buyers seamlessly blend in-store/online. "
            "Implications: retailers must (1) coordinate across channels, (2) provide info online, (3) integrate digital into store experience, "
            "(4) think beyond physical shelf. Shopper marketing now multi-touchpoint process."
        ),
        "source": "Chapter 13, Retailing: Connecting Brands with Consumers",
    },
    {
        "id": "Q102",
        "level": "medium",
        "question": "Tại sao nhiều retailers khó differentiate hiện nay? Solutions là gì?",
        "ground_truth": (
            "Problems: (1) product assortments looking alike - same brands everywhere, (2) service differentiation eroded - discounters add services, "
            "department stores trim, (3) price-sensitive customers - no reason pay more for identical brands. "
            "Solutions: (1) clearly define target market và positioning, (2) highly targeted assortment hoặc exclusive merchandise, "
            "(3) experiential retailing - create unique atmosphere, (4) exceptional service/loyalty programs. Can't rely on products alone anymore."
        ),
        "source": "Chapter 13, Retailer Marketing Decisions",
    },
    {
        "id": "Q103",
        "level": "medium",
        "question": "Experiential retailing là gì? Tại sao stores increasingly focus on experiences?",
        "ground_truth": (
            "Create unique store experiences beyond just selling products - use layout, lighting, music, colors, scents, activities. "
            "Why: (1) differentiation khi products similar, (2) create emotional connections, (3) encourage longer visits/higher spending, "
            "(4) build brand community, (5) combat showrooming - give reasons visit store. "
            "Examples: Apple stores (product experiences), Restoration Hardware galleries (live the furniture). Stores become environments to experience."
        ),
        "source": "Chapter 13, Product Assortment and Services Decision",
    },
    {
        "id": "Q104",
        "level": "medium",
        "question": "Showrooming vs webrooming - implications cho retailers và strategies to address?",
        "ground_truth": (
            "Showrooming: examine in store → buy online cheaper. Threat to store retailers. "
            "Webrooming: research online → buy in store. Opportunity. "
            "Strategies: (1) price-matching policies, (2) highlight in-store advantages (immediate, service, returns), "
            "(3) train associates với tablets to help research, (4) exclusive merchandise, (5) integrate channels - make easy to buy either way. "
            "Convert showroomers into buyers by adding value beyond price."
        ),
        "source": "Chapter 13, Growth of Direct, Online, Mobile, and Social Media Retailing",
    },
    {
        "id": "Q105",
        "level": "medium",
        "question": "Omni-channel retailing requires gì? Tại sao critical for today's retailers?",
        "ground_truth": (
            "Requirements: (1) integrate ALL channels (in-store, online, mobile, social) into seamless experience, (2) consistent inventory/pricing across channels, "
            "(3) flexible fulfillment (buy online pickup in store, ship from store), (4) unified customer data, (5) train employees for omni-channel mindset. "
            "Critical vì: today's shoppers shift seamlessly across channels. Omni-channel shoppers more valuable (8x according to Macy's). "
            "Must be 'available where and when consumers look for you.'"
        ),
        "source": "Chapter 13, The Need for Omni-Channel Retailing",
    },
    # ===========================================================================
    # CHAPTER 14: INTEGRATED MARKETING COMMUNICATIONS (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q106",
        "level": "medium",
        "question": "Tại sao Integrated Marketing Communications (IMC) ngày càng quan trọng?",
        "ground_truth": (
            "Problems without IMC: (1) messages từ different departments conflict (ads vs website vs social media), "
            "(2) consumers don't distinguish sources - merge into single brand message, (3) confusion → weak brand image/positioning. "
            "Need IMC vì: (1) media fragmentation, (2) explosion of touchpoints, (3) consumers bombarded với messages. "
            "IMC carefully integrates all channels to deliver clear, consistent, compelling message. Coordinate content across paid/owned/earned/shared channels."
        ),
        "source": "Chapter 14, The Need for Integrated Marketing Communications",
    },
    {
        "id": "Q107",
        "level": "medium",
        "question": "New marketing communications model khác old mass marketing model như thế nào?",
        "ground_truth": (
            "Old: mass marketing, standardized products, mass media (TV/print), one-way communication, interrupt và force-feed messages. "
            "New: targeted marketing, fragmented markets, digital/social media, two-way engagement, consumers empowered (find own info, create content). "
            "Shift from 'telling and selling' → engaging conversations. Marketers become content managers across fluid mix of channels. "
            "Digital-first approach growing but traditional media still important - need integrated mix."
        ),
        "source": "Chapter 14, The New Marketing Communications Model",
    },
    {
        "id": "Q108",
        "level": "medium",
        "question": "So sánh push strategy với pull strategy trong promotion mix. Khi nào dùng mỗi loại?",
        "ground_truth": (
            "Push: producer promotes TO channel members → they push to consumers. Dùng khi: (1) low brand loyalty, (2) impulse purchases, "
            "(3) product benefits understood, (4) B2B markets. Personal selling quan trọng. "
            "Pull: producer promotes TO final consumers → they demand from channel. Dùng khi: (1) high brand loyalty, (2) high involvement purchases, "
            "(3) need create awareness/demand. Advertising/consumer promotion key. Most companies combine both strategies."
        ),
        "source": "Chapter 14, Shaping the Overall Promotion Mix",
    },
    {
        "id": "Q109",
        "level": "medium",
        "question": "4 methods for setting promotion budget - ưu nhược điểm?",
        "ground_truth": (
            "(1) Affordable: spend what can afford. Easy nhưng ignores ROI, opportunities. "
            "(2) Percentage-of-sales: % of sales/forecast. Simple, ties to revenue nhưng backwards (sales cause promotion, not reverse). "
            "(3) Competitive-parity: match competitors. Safe nhưng assumes competitors right, no differentiation. "
            "(4) Objective-and-task: define objectives → tasks → costs. Most logical, forces thinking nhưng difficult to execute. Best practice: objective-and-task."
        ),
        "source": "Chapter 14, Setting the Total Promotion Budget",
    },
    {
        "id": "Q110",
        "level": "medium",
        "question": "Content marketing khác traditional advertising như thế nào? Role của marketers changed?",
        "ground_truth": (
            "Traditional advertising: create and place ads, one-way push messages. "
            "Content marketing: create/inspire/share brand messages và conversations WITH and AMONG consumers across paid/owned/earned/shared channels. "
            "Marketer role shift: from 'ad creators' → 'content marketing managers'. Focus on context/channels, map customer journey, start conversations leading to engagement. "
            "Integration critical - blend traditional và new media for best customer experiences."
        ),
        "source": "Chapter 14, Content Marketing definition",
    },
    # ===========================================================================
    # CHAPTER 15: ADVERTISING AND PUBLIC RELATIONS (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q111",
        "level": "medium",
        "question": "Phân biệt informative, persuasive, và reminder advertising. Product life cycle stage affect choice?",
        "ground_truth": (
            "Informative: build primary demand, new products, inform market - introduction stage. "
            "Persuasive: build selective demand/brand preference, convince to buy our brand - growth/maturity với competition. Includes comparative advertising. "
            "Reminder: maintain relationships, keep brand top-of-mind - mature products. "
            "Advertising objectives must align với marketing strategy và PLC stage. Different stages need different communication approaches."
        ),
        "source": "Chapter 15, Setting Advertising Objectives",
    },
    {
        "id": "Q112",
        "level": "medium",
        "question": "Madison & Vine concept là gì? Tại sao advertisers move toward advertainment?",
        "ground_truth": (
            "Madison & Vine: merge advertising với entertainment. "
            "Advertainment: brand integrations, product placements, branded entertainment content. "
            "Why shift: (1) ad clutter overwhelming, (2) consumers skip traditional ads, (3) need engage not interrupt, "
            "(4) entertainment more shareable, (5) native advertising blends with content. "
            "Make advertising something consumers WANT to experience. Trade-off: less direct control over message nhưng higher engagement."
        ),
        "source": "Chapter 15, Advertising Strategy section on Madison & Vine",
    },
    {
        "id": "Q113",
        "level": "medium",
        "question": "Tại sao measuring advertising effectiveness và ROI challenging? Methods to evaluate?",
        "ground_truth": (
            "Challenges: (1) multiple factors affect sales (product, price, place, promotion, economy, competition), "
            "(2) hard isolate advertising's specific impact, (3) long-term brand-building vs short-term sales, (4) digital environment fast-paced. "
            "Evaluation methods: (1) Communication effects - pre/post-testing, measure message delivery/perception, "
            "(2) Sales/profit effects - historical data analysis, experiments. Focus on both immediate response AND long-term relationships."
        ),
        "source": "Chapter 15, Evaluating Advertising Effectiveness and Return on Investment",
    },
    {
        "id": "Q114",
        "level": "medium",
        "question": "Public Relations có advantages gì over paid advertising? Nhưng challenges?",
        "ground_truth": (
            "Advantages: (1) high credibility - consumers trust editorial hơn ads, (2) reach skeptical buyers, (3) dramatize company/product, "
            "(4) much lower cost, (5) viral potential qua media coverage/social sharing. "
            "Challenges: (1) less control over message, (2) underutilized by companies, (3) hard to measure impact directly, "
            "(4) requires newsworthy content, (5) can backfire if managed poorly. Despite challenges, PR increasingly important trong digital age."
        ),
        "source": "Chapter 15, Public Relations",
    },
    {
        "id": "Q115",
        "level": "medium",
        "question": "Consumer-generated content (CGC) trong advertising có benefits và risks gì?",
        "ground_truth": (
            "Benefits: (1) authentic/believable - real customers, (2) engage customers deeply - become brand partners, "
            "(3) cost-effective, (4) shareable/viral potential, (5) fresh creative ideas. "
            "Risks: (1) quality inconsistent, (2) off-brand messages, (3) negative content, (4) less control. "
            "Best practice: provide guidelines, curate submissions, combine với professional content. Examples: Converse 'Made By You', contest campaigns."
        ),
        "source": "Chapter 15, Message Execution discussing consumer-generated content",
    },
    # ===========================================================================
    # CHAPTER 16: PERSONAL SELLING AND SALES PROMOTION (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q116",
        "level": "medium",
        "question": "Tại sao sales force coordination với marketing critical? Consequences of poor coordination?",
        "ground_truth": (
            "Sales force là company's direct link to customers, represent company TO customers và customers TO company. "
            "Poor coordination consequences: (1) mixed messages to customers, (2) damaged relationships, (3) lost sales opportunities, "
            "(4) internal conflict, (5) poor performance. "
            "Solutions: joint meetings, shared objectives, integrated systems, dedicated liaisons, unified CRM. Both must work together để create customer value."
        ),
        "source": "Chapter 16, Managing the Sales Force intro",
    },
    {
        "id": "Q117",
        "level": "medium",
        "question": "So sánh territorial, product, và customer sales force structures",
        "ground_truth": (
            "Territorial: mỗi rep assigned geographic area, sell all products. Advantages: clear responsibilities, travel efficient, know local market. "
            "Product: specialize by product line. Advantages: product knowledge, technical products. "
            "Customer: organize by customer/industry. Advantages: build relationships, understand needs better. "
            "Most companies use complex structures combining elements. Choice depends on: products, customers, company size."
        ),
        "source": "Chapter 16, Designing the Sales Force Strategy and Structure",
    },
    {
        "id": "Q118",
        "level": "medium",
        "question": "Team selling advantages và when to use? Challenges?",
        "ground_truth": (
            "Team selling: multidisciplinary teams service large/complex accounts. "
            "When use: (1) complex products, (2) large accounts, (3) need multiple expertise, (4) high-value sales. "
            "Advantages: comprehensive solutions, deeper relationships, coordinate company resources. "
            "Challenges: expensive, coordination complexity, potential conflicts, requires cultural shift. "
            "Growing due to product complexity và customer demands. Virtual communication enables remote teaming."
        ),
        "source": "Chapter 16, Team Selling",
    },
    {
        "id": "Q119",
        "level": "medium",
        "question": "Value selling vs price-cutting - fundamental difference và long-term implications",
        "ground_truth": (
            "Price-cutting: lower price to win sale, erodes margins, trains customers to expect discounts, commodity competition. "
            "Value selling: demonstrate superior customer value created, justify price with benefits/ROI, build relationships on value not price. "
            "Long-term: value selling creates loyal customers willing pay premium; price-cutting creates deal-prone customers, margin pressure. "
            "Challenge: transform salespeople into value advocates not price cutters."
        ),
        "source": "Chapter 16, Personal Selling and Managing Customer Relationships - Value Selling",
    },
    {
        "id": "Q120",
        "level": "medium",
        "question": "Social selling transform personal selling process như thế nào?",
        "ground_truth": (
            "Traditional: salespeople initiate contact, control information, close sales. "
            "Social selling: use online/mobile/social media to (1) engage customers earlier in buying process, (2) monitor customer conversations, "
            "(3) provide insights, (4) build relationships, (5) augment effectiveness. "
            "Customers now research independently → sales shifts to relationship building/problem solving. "
            "Technology augments salespeople, not replaces. Digital tools extend reach nhưng human touch still crucial."
        ),
        "source": "Chapter 16, Social Selling: Online, Mobile, and Social Media Tools",
    },
    # ===========================================================================
    # CHAPTER 17: DIRECT, ONLINE, SOCIAL MEDIA, MOBILE MARKETING (5 questions)
    # ===========================================================================
    {
        "id": "Q121",
        "level": "medium",
        "question": "Direct và digital marketing benefits cho both buyers và sellers - explain cả hai perspectives",
        "ground_truth": (
            "Buyer benefits: (1) convenient - shop anytime/anywhere, (2) easy/private, (3) access to wealth of info, (4) interactive/immediate, (5) customization. "
            "Seller benefits: (1) relationship building tool, (2) cost-effective vs store/sales force, (3) target narrowly, "
            "(4) personalized offers, (5) flexible - adjust quickly, (6) measure results easily. Direct marketing enables one-to-one relationships at scale."
        ),
        "source": "Chapter 17, Benefits of Direct and Digital Marketing to Buyers and Sellers",
    },
    {
        "id": "Q122",
        "level": "medium",
        "question": "Marketing websites vs brand community websites - purposes khác nhau?",
        "ground_truth": (
            "Marketing websites: designed to engage customers và move them closer to purchase/transaction. E-commerce focus, clear paths to buy. "
            "Brand community websites: build customer relationships, engagement, loyalty. Not primarily selling - create experiences, dialogue, community. "
            "Examples: brand fans sites, forums, content hubs. Both important nhưng different roles trong customer journey. Many brands need cả hai."
        ),
        "source": "Chapter 17, Online Marketing",
    },
    {
        "id": "Q123",
        "level": "medium",
        "question": "Social media marketing có advantages nhưng also unique challenges - explain both",
        "ground_truth": (
            "Advantages: (1) targeted/personal, (2) interactive/engagement, (3) immediate/timely, (4) cost-effective, (5) viral potential. "
            "Challenges: (1) user-controlled - consumers have power, (2) hard to measure ROI, (3) time-consuming to manage, "
            "(4) negative feedback public/viral, (5) platforms constantly changing, (6) difficult to monetize for platforms themselves. "
            "Must provide value để customers engage, cannot force."
        ),
        "source": "Chapter 17, Social Media Marketing",
    },
    {
        "id": "Q124",
        "level": "medium",
        "question": "Mobile marketing opportunities unique vì mobile devices có characteristics gì?",
        "ground_truth": (
            "Mobile unique vì: (1) ubiquitous - always with consumer, (2) location-aware - GPS targeting, (3) personal - intimate device, "
            "(4) immediate - real-time engagement, (5) always-on connectivity. "
            "Opportunities: engage consumers 'in the moment' they're most receptive, location-based offers, frictionless buying, integrate into daily life. "
            "Challenge: provide value not intrusion. Mobile ads must be highly relevant và timely."
        ),
        "source": "Chapter 17, Mobile Marketing",
    },
    {
        "id": "Q125",
        "level": "medium",
        "question": "Traditional direct mail vẫn còn relevant trong digital age? Why or why not?",
        "ground_truth": (
            "Still relevant vì: (1) tangible - physical experience computers can't match, (2) highly selective targeting, (3) flexible formats, "
            "(4) personalization, (5) measurable, (6) no ad clutter online, (7) emotional connection. "
            "However: slower, more expensive than digital, environmental concerns. "
            "Best use: integrated campaigns combining direct mail với digital for maximum impact. Permission-based targeting critical to avoid 'junk mail' perception."
        ),
        "source": "Chapter 17, Direct-Mail Marketing",
    },
    # ===========================================================================
    # CHAPTER 18: CREATING COMPETITIVE ADVANTAGE (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q126",
        "level": "medium",
        "question": "Competitor myopia là gì? Tại sao dangerous và examples?",
        "ground_truth": (
            "Focus quá hẹp on current competitors, miss emerging threats từ ngoài traditional industry boundaries. "
            "Dangerous vì: disrupted by unexpected competitors. "
            "Example: Kodak focused on film competitors, missed digital threat. "
            "Must identify competitors from both industry perspective (companies making similar products) VÀ market perspective (companies satisfying same customer needs). "
            "Broader market view reveals more competitors nhưng helps avoid myopia."
        ),
        "source": "Chapter 18, Identifying Competitors - Competitor Myopia",
    },
    {
        "id": "Q127",
        "level": "medium",
        "question": "Blue Ocean Strategy khác traditional competitive strategy như thế nào?",
        "ground_truth": (
            "Traditional (Red Ocean): compete in existing market space, beat competition, exploit demand, make value-cost trade-off. "
            "Blue Ocean: create uncontested market space, make competition irrelevant, create và capture new demand, break value-cost trade-off. "
            "Instead of fighting, create new category. Examples: Apple iPad, Cirque du Soleil. "
            "Risk: eventually others follow → must continue innovate để maintain advantage."
        ),
        "source": "Chapter 18, Selecting Competitors - Blue Ocean Strategy",
    },
    {
        "id": "Q128",
        "level": "medium",
        "question": "So sánh strategies cho market leaders, challengers, followers, và nichers",
        "ground_truth": (
            "Leader: expand total demand, protect share (innovation, defend), expand share carefully. "
            "Challenger: attack leader hoặc smaller firms, full frontal or indirect. "
            "Follower: don't attack, learn from leader, differentiate slightly, lower costs/risks. "
            "Nicher: serve small specialized segments, deep customer knowledge, premium prices. "
            "Each requires different approach. All must monitor competitors và deliver superior customer value regardless of strategy."
        ),
        "source": "Chapter 18, Competitive Positions",
    },
    {
        "id": "Q129",
        "level": "medium",
        "question": "Customer-centered vs competitor-centered orientation - risks của mỗi approach?",
        "ground_truth": (
            "Competitor-centered risks: (1) obsess over competitors' moves, (2) reactive not proactive, (3) miss real customer needs, (4) imitate thay vì innovate. "
            "Customer-centered risks: (1) ignore competitive threats, (2) slow to respond to competitor moves, (3) competitors steal customers. "
            "Best approach: market-centered - balance both. Watch competitors NHƯNG focus primarily on delivering superior customer value. Customer needs should drive strategy."
        ),
        "source": "Chapter 18, Balancing Customer and Competitor Orientations",
    },
    {
        "id": "Q130",
        "level": "medium",
        "question": "Competitive intelligence system làm gì? Ethical considerations?",
        "ground_truth": (
            "Purpose: gather/analyze/distribute competitor info to managers for strategic decisions. "
            "Functions: (1) identify info needs, (2) collect từ various sources, (3) evaluate/analyze, (4) disseminate actionable insights. "
            "Ethical considerations: (1) use only publicly available info, (2) don't engage in espionage, (3) avoid questionable tactics, (4) respect proprietary info. "
            "Can gain intelligence legitimately - don't need to 'break law or codes of ethics.'"
        ),
        "source": "Chapter 18, Designing a Competitive Intelligence System",
    },
    # ===========================================================================
    # CHAPTER 19: THE GLOBAL MARKETPLACE (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q131",
        "level": "medium",
        "question": "Companies face trade-offs khi decide market entry modes (exporting, joint venture, direct investment). Explain trade-offs.",
        "ground_truth": (
            "Trade-off spectrum: Exporting - lowest commitment/risk/control/profit potential. "
            "Joint venturing (licensing, contract manufacturing, joint ownership) - moderate on all. "
            "Direct investment - highest commitment/risk/control/profit. "
            "More involvement = more control và profit potential NHƯNG also more risk và resources required. "
            "Choice depends on: company resources, desired control, risk tolerance, market conditions."
        ),
        "source": "Chapter 19, Deciding How to Enter the Market",
    },
    {
        "id": "Q132",
        "level": "medium",
        "question": "Standardized global marketing vs adapted global marketing - debate và best approach?",
        "ground_truth": (
            "Standardized: same approach worldwide. Arguments: (1) global convergence, (2) economies of scale, (3) consistent brand image. "
            "Adapted: tailor to each market. Arguments: (1) diverse consumer needs/cultures, (2) marketing concept demands meeting specific needs. "
            "Best approach: 'think globally, act locally' - balance global brand consistency với local adaptation. "
            "Examples: L'Oréal adapts products/marketing to local beauty preferences nhưng maintains global brand. Không all-or-nothing decision."
        ),
        "source": "Chapter 19, Deciding on the Global Marketing Program",
    },
    {
        "id": "Q133",
        "level": "medium",
        "question": "Price escalation problem trong international markets. Causes và strategies to address?",
        "ground_truth": (
            "Causes: products cost more in foreign markets due to: (1) shipping/insurance, (2) tariffs/taxes, (3) intermediary margins, "
            "(4) currency exchange fluctuations, (5) regulatory costs. "
            "Strategies: (1) simplify product versions cho lower costs, (2) manufacture locally, (3) introduce low-cost brands (Motorola Moto G for emerging markets), "
            "(4) adjust value proposition. Internet helping standardize global prices via transparency."
        ),
        "source": "Chapter 19, Price section on international pricing",
    },
    {
        "id": "Q134",
        "level": "medium",
        "question": "Cultural environment major challenge trong global marketing. How marketers should approach?",
        "ground_truth": (
            "Culture affects: (1) consumer needs/wants, (2) buying behaviors, (3) communication interpretations, (4) brand perceptions, (5) business practices. "
            "Approach: (1) deep cultural research, (2) respect local customs/values, (3) adapt products/messages appropriately, "
            "(4) avoid cultural insensitivity, (5) hire local talent, (6) test thoroughly before launch. "
            "Mistakes can be costly. Cultural exchange is two-way - marketing also influences culture. Must balance adaptation với maintaining brand essence."
        ),
        "source": "Chapter 19, Elements of the Global Marketing Environment - Cultural Environment",
    },
    {
        "id": "Q135",
        "level": "medium",
        "question": "Whole-channel view trong international distribution important vì sao?",
        "ground_truth": (
            "Whole-channel view: consider entire global supply chain from seller → final user internationally. "
            "Important vì: (1) distribution systems vary dramatically across countries, (2) infrastructure differences (developing vs developed), "
            "(3) retail structures different, (4) must coordinate across borders, (5) longer/more complex channels internationally. "
            "Can't just replicate domestic model. Must adapt to local conditions while managing integrated global system."
        ),
        "source": "Chapter 19, Distribution Channels",
    },
    # ===========================================================================
    # CHAPTER 20: SUSTAINABLE MARKETING (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q136",
        "level": "medium",
        "question": "Sustainable marketing khác traditional marketing concept như thế nào?",
        "ground_truth": (
            "Traditional marketing concept: satisfy current customer needs profitably. "
            "Sustainable marketing: meet PRESENT needs của consumers/businesses/society WITHOUT compromising FUTURE generations' ability to meet their needs. "
            "Broader view: (1) long-term not just short-term, (2) society not just individual customers, (3) environmental impact, (4) ethical considerations. "
            "Triple bottom line: people, planet, profits. Sustainable companies create value through responsible actions."
        ),
        "source": "Chapter 20, Sustainable Marketing definition",
    },
    {
        "id": "Q137",
        "level": "medium",
        "question": "Major social criticisms của marketing về impact on individual consumers gồm gì?",
        "ground_truth": (
            "(1) High prices: due to distribution costs, advertising/promotion, excessive markups. "
            "(2) Deceptive practices: misleading promotion/packaging/pricing. "
            "(3) High-pressure selling: persuade to buy unwanted. "
            "(4) Shoddy/unsafe products: poor quality/safety. "
            "(5) Planned obsolescence: functional (products wear out) hoặc perceived (style changes). "
            "(6) Poor service to disadvantaged: food deserts, underserved communities. Each criticism có counterarguments from marketers."
        ),
        "source": "Chapter 20, Social Criticisms of Marketing - Impact on Individual Consumers",
    },
    {
        "id": "Q138",
        "level": "medium",
        "question": "Environmentalism different from consumerism như thế nào? Both ảnh hưởng marketing strategies?",
        "ground_truth": (
            "Consumerism: movement strengthen buyer rights/power - focus on consumer protection, information, fair treatment. "
            "Environmentalism: protect environment, minimize harm from marketing/consumption - focus on sustainability, responsible consumption, green practices. "
            "Both pressure companies to act responsibly. Marketing impacts: (1) product decisions (safety, green), (2) pricing transparency, "
            "(3) sustainable supply chains, (4) honest communications, (5) corporate social responsibility programs. Complement each other trong promoting sustainable marketing."
        ),
        "source": "Chapter 20, Consumer Actions - Consumerism và Environmentalism sections",
    },
    {
        "id": "Q139",
        "level": "medium",
        "question": "5 sustainable marketing principles companies should follow - briefly explain each",
        "ground_truth": (
            "(1) Consumer-oriented: view from customer perspective, focus needs. "
            "(2) Customer value: invest in product improvements for long-term loyalty, not just short-term tactics. "
            "(3) Innovative: continuously seek improvements. "
            "(4) Sense-of-mission: define purpose beyond profit, guide decisions. "
            "(5) Societal: balance consumer wants, company needs, society's long-term interests. "
            "Together create sustainable marketing that enhances long-term system performance."
        ),
        "source": "Chapter 20, Sustainable Marketing Principles",
    },
    {
        "id": "Q140",
        "level": "medium",
        "question": "Marketing ethics - two philosophies về corporate responsibility. Which better và why?",
        "ground_truth": (
            "Philosophy 1: let market/legal system decide - do what law allows, competitive pressures guide. "
            "Philosophy 2 (Enlightened): company should have social conscience, apply high ethical standards BEYOND what system requires, seek long-term consumer welfare. "
            "Better: Philosophy 2 - vì (1) builds trust/reputation, (2) avoids future regulations, (3) attracts value-conscious consumers, (4) sustainable long-term. "
            "Ethics should guide decisions, not just minimum legal compliance. Corporate culture critical."
        ),
        "source": "Chapter 20, Marketing Ethics",
    },
    # ===========================================================================
    # CROSS-CHAPTER LEVEL 3: HARD INTEGRATION QUESTIONS (5 questions from generating_test_4.md)
    # ===========================================================================
    {
        "id": "Q141",
        "level": "hard",
        "question": (
            "Một company muốn launch sản phẩm mới vào international market. Integrate strategic decisions về: "
            "product development approach, market entry mode, pricing strategy, distribution channels, và promotional methods. "
            "Factors nào affect each decision và how they interrelate?"
        ),
        "ground_truth": (
            "Integrated approach: (1) Product Development (Ch.9): Customer-centered, involve local customers trong idea generation/concept testing để ensure fit với cultural needs. "
            "Decision: straight extension vs adaptation vs invention depends on: local preferences, regulations, costs. "
            "(2) Market Selection (Ch.19): Analyze environment - demographic, economic, political-legal, cultural factors. Assess: market potential, risks, infrastructure, competitive landscape. "
            "(3) Entry Mode (Ch.19): Exporting (low risk, test market) → Joint venture (learn local, share risk) → Direct investment (full control, long-term). "
            "Choice affects control over marketing mix, resource requirements, profit potential, speed to market. "
            "(4) Pricing (Ch.10, 19): Must consider price escalation (shipping, tariffs, margins), local income levels, local competition, currency, value perceptions vary by culture. "
            "(5) Distribution (Ch.12, 19): Vary dramatically by country. Must assess retail structure, infrastructure, local preferences. Design whole-channel view. "
            "(6) Promotion (Ch.14, 15, 19): IMC critical - integrate traditional/digital. Message: standardize core theme or adapt?. Media availability varies. "
            "All must align với overall strategy và local realities."
        ),
        "source": "Integration of Ch.9 (product development), Ch.10 (pricing), Ch.12 (channels), Ch.14-15 (promotion), Ch.19 (global decisions)",
    },
    {
        "id": "Q142",
        "level": "hard",
        "question": (
            "Analyze làm thế nào digital transformation fundamentally changed cả downstream (retailing, customer engagement) "
            "VÀ upstream (supply chain, channel management) của value delivery network"
        ),
        "ground_truth": (
            "DOWNSTREAM Transformations: (1) Retailing Revolution (Ch.13): Omni-channel buying replaces linear shopping. Showrooming/webrooming blur online-offline. "
            "Zero moment of truth (online research) precedes purchase. Need seamless integration across touchpoints. "
            "(2) Customer Engagement (Ch.14, 17): From mass marketing → micro-targeted communities. From one-way ads → two-way conversations. "
            "Content marketing replaces interruption marketing. Social media enables customer co-creation. Mobile enables real-time, location-based engagement. "
            "UPSTREAM Transformations: (1) Channel Management (Ch.12): Disintermediation threatens traditional intermediaries. New digital intermediaries emerge. "
            "Multichannel systems more complex. Need PRM systems to coordinate partners. "
            "(2) Supply Chain (Ch.12): RFID/automation in warehousing. Real-time inventory visibility. Demand sensing vs demand forecasting. "
            "Integration Challenges: Channel conflict (online vs retail partners), data integration (unified customer view), inventory coordination, consistent experience. "
            "Conclusion: Digital fundamentally restructures entire value network. Success requires thinking of online/offline as INTEGRATED SYSTEM."
        ),
        "source": "Integration of Ch.12 (channels, disintermediation), Ch.13 (omni-channel retailing), Ch.14 (new communications model), Ch.17 (digital marketing)",
    },
    {
        "id": "Q143",
        "level": "hard",
        "question": (
            "Một established brand trong mature PLC stage facing declining sales và increased competition. "
            "Design comprehensive turnaround strategy integrating: PLC management, competitive positioning, pricing approach, channel strategy, và sustainable marketing principles."
        ),
        "ground_truth": (
            "Diagnosis Phase: (1) Research customers (Ch.4, 5) - understand why customers leaving, competitor analysis, environmental shifts, customer insights. "
            "Strategic Framework: (1) PLC Rejuvenation (Ch.9) - Market modification (find new users, uses, usage), Product modification (improve features, modernize), "
            "Marketing mix modification (refresh pricing/promotion/distribution). "
            "(2) Competitive Repositioning (Ch.7, 18) - Assess current position vs competitors, options based on market position (leader/challenger/follower), "
            "may need fundamental repositioning to new target/value proposition. Consider blue ocean approach. "
            "(3) Pricing Realignment (Ch.10, 11) - Avoid death by discount - erodes brand. Reframe value proposition, emphasize quality = long-term value. "
            "Value-added pricing, good-value pricing for entry-tier without diluting core. "
            "(4) Channel Innovation (Ch.12, 13) - Evaluate current channels, consider new channels (digital direct-to-consumer, omni-channel integration). "
            "(5) Integrated Communications (Ch.14, 15) - Refresh brand message while maintaining equity, leverage digital/social media. "
            "(6) Sustainable Marketing (Ch.20) - Integrate sense-of-mission, appeal to societal concerns, innovation focus. "
            "Critical balance: address immediate sales decline NHƯNG protect long-term positioning."
        ),
        "source": "Integration of Ch.4 (research), Ch.7 (repositioning), Ch.9 (PLC maturity), Ch.10-11 (pricing), Ch.12-13 (channels), Ch.14-15 (communications), Ch.18 (competitive strategy), Ch.20 (sustainability)",
    },
    {
        "id": "Q144",
        "level": "hard",
        "question": (
            "Compare và contrast làm thế nào small innovative company vs large established company should approach: "
            "new product development, market entry, competitive strategy, channel decisions, và resource allocation. What are relative advantages của each?"
        ),
        "ground_truth": (
            "Small Innovative Company: (1) NPD (Ch.9): agile, fail fast, customer-intimate, creative freedom. Crowdsource ideas, lean development, beta test continuously. "
            "(2) Market Entry (Ch.7, 18): concentrated/niche marketing - serve overlooked segments. Nimble, closer to customers, authentic. "
            "(3) Competitive Strategy (Ch.18): Cannot compete on scale, cost leadership. CAN differentiate on innovation, service, specialization. "
            "Indirect attack, focus differentiation, build cult following. Digital leverage equalizes playing field. "
            "(4) Channels (Ch.12, 13): Flexible, innovative channels, direct relationships. Selective/exclusive distribution, direct-to-consumer online. "
            "Large Established Company: (1) NPD (Ch.9): extensive R&D, can afford risks, testing resources. Bureaucratic, slow, risk-averse. "
            "(2) Market Entry (Ch.7, 18): undifferentiated, differentiated, or multiple segments. Resources to serve multiple segments simultaneously. "
            "(3) Competitive Strategy (Ch.18): If leader - expand demand, protect share through innovation. Economies of scale, brand recognition, distribution power. "
            "(4) Channels (Ch.12, 13): Channel power, multiple channels simultaneously, can support intermediaries. Intensive distribution, vertical integration possible. "
            "Comparative Insights: Small advantages - speed, agility, customer intimacy, authenticity, risk-taking freedom, digital leverage. "
            "Large advantages - resources, brand equity, distribution power, R&D capabilities, survive failures. "
            "Both Must: deliver superior customer value, understand customers deeply, adapt to environment, integrate marketing mix, act sustainably."
        ),
        "source": "Integration of Ch.7 (marketing), Ch.9 (NPD), Ch.12 (channels), Ch.18 (competitive strategies)",
    },
    {
        "id": "Q145",
        "level": "hard",
        "question": (
            "Trong digital age, explain fundamental tensions between: (a) personalization vs privacy, (b) channel integration vs channel conflict, "
            "(c) automation vs human touch, (d) data-driven decisions vs creative intuition. How should marketers balance these tensions?"
        ),
        "ground_truth": (
            "(A) Personalization vs Privacy: More data enables better targeting/customization NHƯNG raises privacy concerns. "
            "Balance: Transparency về data usage, provide value exchange, permission-based marketing, follow regulations, let consumers control preferences. "
            "(B) Channel Integration vs Channel Conflict: Direct digital sales grow NHƯNG alienate retail partners. "
            "Balance: Route online sales THROUGH partners (Volvo approach), price-match policies, differentiate channel offerings, share data to help partners compete. "
            "(C) Automation vs Human Touch: Technology efficiency vs personal relationships. "
            "Balance: Technology handles routine, humans handle complex/emotional. Use automation to empower people, not replace. Personal touch for high-value customers. "
            "(D) Data-Driven vs Creative Intuition: Analytics precision vs creative breakthroughs. "
            "Balance: Use data to inform NOT dictate decisions. Analytics for optimization, creativity for differentiation. Creative concept first, then test and refine with data. "
            "Overarching Principles: Customer Value First - all tensions should resolve toward creating superior customer value. "
            "Integration Mindset - not either/or but both/and. Transparency - ethical practices build trust that enables personalization. "
            "Long-term View - prioritize relationships over short-term efficiency. Test and Learn continuously. "
            "These tensions are NOT problems to eliminate but paradoxes to manage. Best marketers skillfully integrate opposing forces."
        ),
        "source": "Integration of tensions throughout book - privacy (Ch.4, 7, 17), channels (Ch.12, 13), automation (Ch.16), data (Ch.4), ethics (Ch.20)",
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
