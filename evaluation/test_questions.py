"""
Marketing Knowledge Test Questions

Curated questions for testing marketing knowledge retrieval and reasoning.
These questions focus on conceptual understanding and problem-solving,
NOT specific case studies or company examples.

Coverage:
- Q1-Q12: Original mixed-level questions (simple, medium, hard)
- Q147-Q186: Basic theory questions (2 per chapter for all 18 chapters)

Source: Principles of Marketing 17th Edition - Kotler & Armstrong
"""

TEST_QUESTIONS = [
    # ===========================================================================
    # LEVEL 1: Simple - Information from single section
    # ===========================================================================
    {
        "id": "Q1",
        "level": "simple",
        "question": "Marketing Myopia là gì và làm thế nào để tránh nó?",
        "ground_truth": (
            "Marketing Myopia (tật cận thị marketing) là sai lầm khi công ty chú ý quá nhiều đến "
            "sản phẩm cụ thể mà họ cung cấp thay vì tập trung vào lợi ích và trải nghiệm mà sản phẩm "
            "đó mang lại cho khách hàng. Ví dụ: một nhà sản xuất mũi khoan có thể nghĩ khách hàng "
            "cần mũi khoan, nhưng thực ra khách hàng cần một lỗ khoan. Để tránh marketing myopia, "
            "công ty cần định nghĩa doanh nghiệp theo nhu cầu khách hàng chứ không phải theo sản phẩm."
        ),
        "source": "Chapter 1, Section 'Market Offerings—Products, Services, and Experiences'",
    },
    {
        "id": "Q2",
        "level": "simple",
        "question": "Định nghĩa Marketing và giải thích mục tiêu kép của nó là gì?",
        "ground_truth": (
            "Marketing được định nghĩa là quá trình mà các công ty thu hút khách hàng, xây dựng "
            "mối quan hệ khách hàng bền chặt, và tạo ra giá trị khách hàng nhằm thu về giá trị "
            "từ khách hàng. Mục tiêu kép của marketing là: (1) Thu hút khách hàng mới bằng cách "
            "hứa hẹn giá trị vượt trội, và (2) Giữ chân và phát triển khách hàng hiện tại bằng "
            "cách cung cấp sự hài lòng."
        ),
        "source": "Chapter 1, Section 'Marketing Defined'",
    },
    {
        "id": "Q3",
        "level": "simple",
        "question": "BCG Growth-Share Matrix gồm những loại SBU nào và chiến lược cho mỗi loại là gì?",
        "ground_truth": (
            "BCG Growth-Share Matrix gồm 4 loại SBU: "
            "(1) Stars - tăng trưởng cao, thị phần cao: đầu tư mạnh để duy trì vị trí; "
            "(2) Cash Cows - tăng trưởng thấp, thị phần cao: 'vắt sữa' để tài trợ cho các SBU khác; "
            "(3) Question Marks - tăng trưởng cao, thị phần thấp: cần quyết định đầu tư để thành Stars hoặc loại bỏ; "
            "(4) Dogs - tăng trưởng thấp, thị phần thấp: cân nhắc loại bỏ hoặc thu hẹp."
        ),
        "source": "Chapter 2, Section 'The Boston Consulting Group Approach'",
    },
    {
        "id": "Q4",
        "level": "simple",
        "question": "Phân biệt Needs, Wants và Demands trong marketing. Cho ví dụ minh họa.",
        "ground_truth": (
            "Needs (Nhu cầu): Là trạng thái thiếu hụt cảm thấy, bao gồm nhu cầu vật lý (thức ăn, quần áo), "
            "nhu cầu xã hội (thuộc về, tình cảm), và nhu cầu cá nhân (kiến thức, tự thể hiện). "
            "Wants (Mong muốn): Là hình thức mà nhu cầu thể hiện khi được định hình bởi văn hóa và tính cách. "
            "Ví dụ: người cần thức ăn nhưng muốn Big Mac. "
            "Demands (Nhu cầu có khả năng chi trả): Là mong muốn được hỗ trợ bởi sức mua. "
            "Khi có sức mua, wants trở thành demands."
        ),
        "source": "Chapter 1, Section 'Customer Needs, Wants, and Demands'",
    },
    {
        "id": "Q5",
        "level": "simple",
        "question": "Mission Statement là gì và nó nên tập trung vào điều gì để hiệu quả?",
        "ground_truth": (
            "Mission Statement là tuyên bố về mục đích của tổ chức - những gì tổ chức muốn hoàn thành "
            "trong môi trường rộng lớn hơn. Để hiệu quả, mission statement nên: "
            "(1) Định hướng theo thị trường và nhu cầu khách hàng, không phải theo sản phẩm/công nghệ; "
            "(2) Có ý nghĩa và cụ thể; (3) Phù hợp với môi trường thị trường; "
            "(4) Dựa trên năng lực cốt lõi; (5) Truyền cảm hứng và động lực."
        ),
        "source": "Chapter 2, Section 'Defining a Market-Oriented Mission'",
    },
    # ===========================================================================
    # LEVEL 2: Medium - Information from multiple sections within same chapter
    # ===========================================================================
    {
        "id": "Q6",
        "level": "medium",
        "question": "Mô tả 5 bước trong Marketing Process và giải thích mối quan hệ giữa chúng.",
        "ground_truth": (
            "Marketing Process gồm 5 bước: "
            "(1) Understand the marketplace and customer needs - Hiểu thị trường và nhu cầu khách hàng; "
            "(2) Design a customer value-driven marketing strategy - Thiết kế chiến lược marketing hướng đến giá trị; "
            "(3) Construct an integrated marketing program - Xây dựng chương trình marketing tích hợp (4Ps); "
            "(4) Engage customers, build profitable relationships - Thu hút và xây dựng mối quan hệ có lợi; "
            "(5) Capture value from customers - Thu về giá trị từ khách hàng. "
            "Trong 4 bước đầu, công ty tạo giá trị cho khách hàng; ở bước cuối, công ty thu về giá trị "
            "từ khách hàng dưới dạng lợi nhuận và customer lifetime value."
        ),
        "source": "Chapter 1, multiple sections from 'The Marketing Process' to 'Capturing Value'",
    },
    {
        "id": "Q7",
        "level": "medium",
        "question": "So sánh 5 marketing management orientations và khi nào nên áp dụng từng loại?",
        "ground_truth": (
            "5 marketing orientations: "
            "(1) Production Concept - tập trung hiệu quả sản xuất và phân phối rộng; áp dụng khi cầu > cung; "
            "(2) Product Concept - tập trung cải tiến sản phẩm liên tục; có thể dẫn đến marketing myopia; "
            "(3) Selling Concept - tập trung bán hàng và xúc tiến mạnh; áp dụng cho unsought goods hoặc công suất dư; "
            "(4) Marketing Concept - tập trung hiểu và đáp ứng nhu cầu khách hàng tốt hơn đối thủ; customer-centric; "
            "(5) Societal Marketing Concept - cân bằng giữa mong muốn khách hàng, lợi ích công ty và lợi ích xã hội dài hạn."
        ),
        "source": "Chapter 1, Section 'Customer Value-Driven Marketing Strategy'",
    },
    {
        "id": "Q8",
        "level": "medium",
        "question": "Giải thích Value Chain và Value Delivery Network. Sự khác biệt giữa chúng là gì?",
        "ground_truth": (
            "Value Chain (Chuỗi giá trị nội bộ): Là chuỗi các hoạt động nội bộ công ty để tạo giá trị - "
            "bao gồm thiết kế, sản xuất, marketing, phân phối, hỗ trợ sản phẩm. Mỗi phòng ban phải "
            "phối hợp để tối đa hóa giá trị khách hàng. "
            "Value Delivery Network (Mạng lưới phân phối giá trị): Là mạng lưới bên ngoài gồm công ty, "
            "nhà cung cấp, distributors, và khách hàng cùng hợp tác. Cạnh tranh ngày nay là giữa các "
            "value delivery networks, không chỉ giữa các công ty riêng lẻ."
        ),
        "source": "Chapter 2, Section 'Planning Marketing: Partnering to Build Customer Relationships'",
    },
    {
        "id": "Q9",
        "level": "medium",
        "question": "Product/Market Expansion Grid gồm những chiến lược tăng trưởng nào? Khi nào nên dùng mỗi chiến lược?",
        "ground_truth": (
            "Product/Market Expansion Grid gồm 4 chiến lược: "
            "(1) Market Penetration - tăng doanh số sản phẩm hiện tại trong thị trường hiện tại; dùng khi còn tiềm năng trong thị trường; "
            "(2) Market Development - phát triển thị trường mới cho sản phẩm hiện tại; dùng khi có segment hoặc địa lý chưa khai thác; "
            "(3) Product Development - tạo sản phẩm mới cho thị trường hiện tại; dùng khi khách hàng cần innovation; "
            "(4) Diversification - phát triển sản phẩm mới cho thị trường mới; rủi ro cao nhất nhưng có thể cần khi thị trường cốt lõi bão hòa."
        ),
        "source": "Chapter 2, Section 'Developing Strategies for Growth and Downsizing'",
    },
    # ===========================================================================
    # LEVEL 3: Hard - Requires reasoning across multiple chapters
    # ===========================================================================
    {
        "id": "Q10",
        "level": "hard",
        "question": (
            "Làm thế nào để áp dụng Marketing Process (5 bước) kết hợp với phân tích Marketing Environment "
            "để xây dựng chiến lược marketing hiệu quả cho một sản phẩm mới?"
        ),
        "ground_truth": (
            "Để xây dựng chiến lược hiệu quả, cần kết hợp: "
            "Bước 1 (Understand): Phân tích cả Microenvironment (công ty, suppliers, competitors, khách hàng) "
            "và Macroenvironment (demographic, economic, natural, technological, political, cultural). "
            "Bước 2 (Design Strategy): Dựa trên insights từ environment analysis, xác định target market và positioning. "
            "Bước 3 (Marketing Program): Thiết kế 4Ps phù hợp với điều kiện môi trường. "
            "Bước 4 (Engage): Xây dựng customer relationships phù hợp với xu hướng digital và social của target. "
            "Bước 5 (Capture Value): Đo lường ROI và điều chỉnh theo thay đổi môi trường. "
            "Quan trọng: Phải proactive trong việc respond và adapt với environmental changes."
        ),
        "source": "Integration of Chapter 1 (Marketing Process) and Chapter 3 (Marketing Environment)",
    },
    {
        "id": "Q11",
        "level": "hard",
        "question": (
            "Làm thế nào để cân bằng giữa Marketing Concept và Societal Marketing Concept "
            "trong thời đại sustainability? Đưa ra framework để đánh giá."
        ),
        "ground_truth": (
            "Cân bằng giữa hai concepts đòi hỏi: "
            "Marketing Concept: Tập trung vào customer satisfaction và loyalty. "
            "Societal Marketing Concept: Cân bằng company profits, consumer wants, và society's long-term interests. "
            "Framework đánh giá gồm: (1) Integration: Sustainability phải embedded trong core strategy, không phải add-on; "
            "(2) Transparency: Honest communication về efforts và limitations; "
            "(3) Long-term thinking: Accept short-term costs cho long-term benefits; "
            "(4) Stakeholder approach: Consider impact on all stakeholders; "
            "(5) Measurement: Track cả financial và social/environmental metrics. "
            "Thành công khi 'doing well' và 'doing good' aligned."
        ),
        "source": "Integration of Chapter 1 (Marketing Orientations, Societal Marketing) and Chapter 3 (Natural Environment)",
    },
    {
        "id": "Q12",
        "level": "hard",
        "question": (
            "Phân tích cách digital transformation đã thay đổi từng bước trong Marketing Process. "
            "Những implications nào cho traditional marketing models?"
        ),
        "ground_truth": (
            "Digital transformation thay đổi toàn bộ Marketing Process: "
            "Bước 1 (Understand): Big Data thay focus groups, social listening, real-time feedback. "
            "Bước 2 (Design Strategy): Micro-segmentation dựa trên digital behavior, personalization at scale. "
            "Bước 3 (Marketing Mix): Product co-creation, dynamic pricing, omnichannel distribution, content marketing. "
            "Bước 4 (Engage): Two-way communication thay broadcasting, consumer-generated content, community building. "
            "Bước 5 (Capture Value): Real-time dashboards, engagement metrics, CLV models. "
            "Implications: (1) Marketing mix evolves từ 4Ps chỉ không đủ; "
            "(2) CRM chuyển từ transactional sang engagement-based; "
            "(3) Research liên tục thay periodic; "
            "(4) Segmentation dynamic thay static; "
            "(5) Co-created value thay company-created."
        ),
        "source": "Integration of Chapter 1 (Digital Age, Marketing Process), Chapter 3 (Technology Environment), Chapter 4 (Marketing Analytics)",
    },
    # ===========================================================================
    # BASIC THEORY QUESTIONS - 2 per chapter (36 questions from generating_test_5.md)
    # ===========================================================================
    # CHAPTER 1: MARKETING FUNDAMENTALS
    {
        "id": "Q147",
        "level": "simple",
        "question": "Định nghĩa 'customer-perceived value' và giải thích tại sao nó là yếu tố quyết định trong customer's buying decision?",
        "ground_truth": (
            "Customer-perceived value là sự đánh giá của khách hàng về sự khác biệt giữa tất cả lợi ích (benefits) và "
            "tất cả chi phí (costs) của một market offering so với các đối thủ cạnh tranh. Nó quyết định buying decision vì: "
            "(1) Customers không có thời gian/thông tin để đánh giá chính xác tất cả offerings, (2) Họ phụ thuộc vào perceived value "
            "dựa trên kinh nghiệm/kỳ vọng, (3) Nếu perceived value thấp hơn kỳ vọng → không mua hoặc không quay lại. "
            "Marketers phải deliver on value promise để satisfy customers."
        ),
        "source": "Chapter 1, Customer Value and Satisfaction",
    },
    {
        "id": "Q148",
        "level": "simple",
        "question": "Phân biệt 'customer satisfaction' và 'customer delight'. Tại sao customer delight quan trọng cho long-term success?",
        "ground_truth": (
            "Customer satisfaction: khi perceived performance matches expectations - khách hàng satisfied but not necessarily thrilled. "
            "Customer delight: khi performance EXCEEDS expectations significantly - creates emotional connection và surprise. "
            "Delight quan trọng vì: (1) Delighted customers = emotionally attached, (2) Higher loyalty và advocacy, (3) Share experiences và recommend, "
            "(4) Less price-sensitive, (5) Forgive occasional failures. Companies must aim to delight, not just satisfy, to build lasting relationships."
        ),
        "source": "Chapter 1, Customer Satisfaction",
    },
    # CHAPTER 2: STRATEGIC PLANNING
    {
        "id": "Q149",
        "level": "simple",
        "question": "Business portfolio là gì? Tại sao việc đánh giá và manage portfolio quan trọng cho strategic planning?",
        "ground_truth": (
            "Business portfolio là tập hợp các businesses và products tạo nên công ty. Portfolio analysis là major activity trong strategic planning - "
            "đánh giá businesses để đưa resources vào profitable ones, strengthen/hold/phase out weak ones. "
            "Quan trọng vì: (1) Resources limited, must allocate wisely, (2) Businesses evolve differently, (3) Some need investment, some generate cash, "
            "(4) Environment changes require portfolio adjustments, (5) Ensure balance between growth và stability."
        ),
        "source": "Chapter 2, Designing the Business Portfolio",
    },
    {
        "id": "Q150",
        "level": "simple",
        "question": "SWOT analysis gồm những thành phần nào? Phân biệt internal và external factors trong SWOT.",
        "ground_truth": (
            "SWOT = Strengths, Weaknesses, Opportunities, Threats. "
            "Internal factors (controllable): Strengths - internal capabilities có thể leverage, Weaknesses - internal limitations cần overcome. "
            "External factors (uncontrollable): Opportunities - favorable external factors có thể exploit, Threats - unfavorable external factors phải defend against. "
            "Mục đích: match Strengths với Opportunities, convert Weaknesses/Threats, determine strategic direction."
        ),
        "source": "Chapter 2, Analyzing the Current Business Portfolio - SWOT Analysis",
    },
    # CHAPTER 3: MARKETING ENVIRONMENT
    {
        "id": "Q151",
        "level": "simple",
        "question": "Microenvironment gồm những actors nào? Tại sao mỗi actor quan trọng cho marketing success?",
        "ground_truth": (
            "Microenvironment actors: (1) Company - interdepartmental coordination, (2) Suppliers - provide resources to produce, affect costs/availability, "
            "(3) Marketing intermediaries - help promote/sell/distribute, (4) Competitors - affect positioning/strategy, "
            "(5) Publics - groups với actual/potential interest, (6) Customers - central, understand different types. "
            "Mỗi actor quan trọng vì tạo thành company's immediate operating environment - affect ability to engage và serve customers."
        ),
        "source": "Chapter 3, The Microenvironment",
    },
    {
        "id": "Q152",
        "level": "simple",
        "question": "Macroenvironment forces (PESTLE) gồm những gì? Cho ví dụ về ảnh hưởng của từng force.",
        "ground_truth": (
            "Macroenvironment forces: (1) Demographic - population changes (aging → healthcare), (2) Economic - spending/buying power (recession → value focus), "
            "(3) Natural - environmental sustainability (green products), (4) Technological - new technologies (digital disruption), "
            "(5) Political/Legal - regulations/policies (data privacy laws), (6) Cultural - values/beliefs (health consciousness). "
            "Uncontrollable, shape opportunities và threats cho tất cả companies."
        ),
        "source": "Chapter 3, The Macroenvironment",
    },
    # CHAPTER 4: MARKETING INFORMATION
    {
        "id": "Q153",
        "level": "simple",
        "question": "Marketing Information System (MIS) gồm những components nào? Mỗi component serve purpose gì?",
        "ground_truth": (
            "MIS Components: (1) Internal databases - company's own data (sales, costs, inventory) - provides operational insights, "
            "(2) Competitive marketing intelligence - systematic monitoring of public info about competitors/environment - early warning, "
            "(3) Marketing research - systematic design/collection/analysis for specific decisions - deep insights, "
            "(4) Marketing analytics - tools to analyze big data and derive insights. "
            "Purpose: provide right information to right decision makers at right time."
        ),
        "source": "Chapter 4, Marketing Information Systems",
    },
    {
        "id": "Q154",
        "level": "simple",
        "question": "Marketing research process gồm mấy bước? Mô tả ngắn gọn từng bước.",
        "ground_truth": (
            "4 bước: (1) Defining problem and research objectives - most difficult, set direction (exploratory/descriptive/causal), "
            "(2) Developing research plan - determine exact information needed, sources, approaches, contact methods, sampling, instruments, "
            "(3) Implementing research plan - collect và analyze data, "
            "(4) Interpreting and reporting findings - translate into insights, present to decision makers. "
            "Process ensures systematic, objective approach to gathering needed information."
        ),
        "source": "Chapter 4, Marketing Research",
    },
    # CHAPTER 5: CONSUMER BEHAVIOR
    {
        "id": "Q155",
        "level": "simple",
        "question": "Buyer decision process gồm mấy stages? Mô tả từng stage.",
        "ground_truth": (
            "5 stages: (1) Need recognition - realize problem/need exists, internal/external stimuli, "
            "(2) Information search - gather info from personal/commercial/public/experiential sources, "
            "(3) Evaluation of alternatives - process info, compare brands using evaluative criteria, "
            "(4) Purchase decision - form intention, choose brand, may be affected by others' attitudes/unexpected factors, "
            "(5) Postpurchase behavior - compare expectations vs performance → satisfaction/dissatisfaction → cognitive dissonance. "
            "Marketers must understand và influence each stage."
        ),
        "source": "Chapter 5, The Buyer Decision Process",
    },
    {
        "id": "Q156",
        "level": "simple",
        "question": "4 types of buying decision behavior là gì? Phân loại theo level of involvement và brand differences.",
        "ground_truth": (
            "Phân loại theo involvement (high/low) × brand differences (significant/few): "
            "(1) Complex buying behavior - high involvement + significant differences (xe hơi) → extensive research, "
            "(2) Dissonance-reducing behavior - high involvement + few differences (thảm) → shop around, post-purchase doubt, "
            "(3) Habitual buying behavior - low involvement + few differences (muối) → routine, brand familiarity, "
            "(4) Variety-seeking behavior - low involvement + significant differences (cookies) → try different brands. "
            "Different strategies needed."
        ),
        "source": "Chapter 5, Types of Buying Decision Behavior",
    },
    # CHAPTER 6: BUSINESS BUYER BEHAVIOR
    {
        "id": "Q157",
        "level": "simple",
        "question": "Business buying process gồm mấy stages? So sánh với consumer buying process.",
        "ground_truth": (
            "8 stages (new task full sequence): (1) Problem recognition, (2) General need description, (3) Product specification, "
            "(4) Supplier search, (5) Proposal solicitation, (6) Supplier selection, (7) Order-routine specification, (8) Performance review. "
            "So với consumer: formal hơn, complex hơn (technical specs), involve more people (buying center), longer process, "
            "rational/economic focus hơn. Some stages may skip trong rebuy situations."
        ),
        "source": "Chapter 6, The Business Buying Process",
    },
    {
        "id": "Q158",
        "level": "simple",
        "question": "Buying center gồm những roles nào? Tại sao marketers phải identify tất cả participants?",
        "ground_truth": (
            "5 roles trong buying center: (1) Users - use product, often initiate, have specifications, "
            "(2) Influencers - help define specs, provide info for evaluation, often technical, "
            "(3) Buyers - formal authority to select supplier, negotiate terms, "
            "(4) Deciders - formal/informal power to select/approve suppliers, "
            "(5) Gatekeepers - control info flow to others. "
            "Phải identify all vì: mỗi có different concerns/criteria, missing one có thể mean losing sale."
        ),
        "source": "Chapter 6, Participants in the Business Buying Process",
    },
    # CHAPTER 7: CUSTOMER-DRIVEN MARKETING STRATEGY
    {
        "id": "Q159",
        "level": "simple",
        "question": "Market segmentation là gì? Nêu 4 major variables để segment consumer markets.",
        "ground_truth": (
            "Market segmentation: chia market thành smaller segments với distinct needs/characteristics/behaviors requiring separate strategies. "
            "4 major variables: (1) Geographic - chia theo location (region, city, climate), "
            "(2) Demographic - chia theo age, gender, income, education, family (most popular), "
            "(3) Psychographic - chia theo social class, lifestyle, personality, "
            "(4) Behavioral - chia theo occasions, benefits, user status, usage rate, loyalty. "
            "Companies use multiple bases combined."
        ),
        "source": "Chapter 7, Market Segmentation",
    },
    {
        "id": "Q160",
        "level": "simple",
        "question": "Differentiation và Positioning khác nhau như thế nào? Mối quan hệ giữa chúng?",
        "ground_truth": (
            "Differentiation: thực sự differentiate market offering từ competitors - create superior customer value. "
            "Positioning: arrange offering to occupy clear, distinctive, desirable place in target customers' minds. "
            "Relationship: Differentiation là actual differences, Positioning là how differences perceived. "
            "Process: chọn competitive advantages để differentiate → communicate để establish position. "
            "Must deliver on promise - positioning must reflect actual differentiation."
        ),
        "source": "Chapter 7, Differentiation and Positioning",
    },
    # CHAPTER 8: PRODUCTS, SERVICES, AND BRANDS
    {
        "id": "Q161",
        "level": "simple",
        "question": "3 levels of product là gì? Cho ví dụ minh họa cho từng level.",
        "ground_truth": (
            "3 levels: (1) Core customer value - what buyer really buying, underlying benefit/solution (cosmetics = hope không chỉ chemicals), "
            "(2) Actual product - product/service features, design, quality, brand name, packaging (actual iPhone với design/features), "
            "(3) Augmented product - additional services/benefits (warranty, support, free delivery, installation). "
            "Marketers must think about all 3 levels - customers buy bundles of benefits."
        ),
        "source": "Chapter 8, Levels of Product and Services",
    },
    {
        "id": "Q162",
        "level": "simple",
        "question": "Brand equity là gì? Những elements nào contribute vào strong brand equity?",
        "ground_truth": (
            "Brand equity: differential effect brand knowledge has on consumer response to marketing - positive or negative. "
            "Elements contributing: (1) Brand awareness - recognizable, top-of-mind, (2) Perceived quality - consistent quality, "
            "(3) Brand associations - memories/feelings connected, (4) Brand loyalty - repeat customers, advocacy, "
            "(5) Other proprietary assets - trademarks, patents, relationships. "
            "High equity means customers prefer và pay more, provides leverage in market."
        ),
        "source": "Chapter 8, Brand Equity and Brand Value",
    },
    # CHAPTER 9: NEW PRODUCT DEVELOPMENT AND PLC
    {
        "id": "Q163",
        "level": "simple",
        "question": "New product development process gồm mấy stages? Mô tả ngắn gọn purpose của từng stage.",
        "ground_truth": (
            "8 stages: (1) Idea generation - search for ideas (internal/external sources), "
            "(2) Idea screening - filter to best ideas, (3) Concept development & testing - develop concepts, test với target consumers, "
            "(4) Marketing strategy development - initial strategy plan, (5) Business analysis - review projections, "
            "(6) Product development - create physical product, (7) Test marketing - test in realistic settings, "
            "(8) Commercialization - launch to market. Each stage reduces risks của failure."
        ),
        "source": "Chapter 9, New Product Development Process",
    },
    {
        "id": "Q164",
        "level": "simple",
        "question": "Product Life Cycle (PLC) gồm mấy stages? Marketing objectives và strategies thay đổi như thế nào qua mỗi stage?",
        "ground_truth": (
            "4 stages và strategies: (1) Introduction - slow growth, high costs, build awareness/trial, basic product, high price, "
            "(2) Growth - rapid acceptance, improve product, expand distribution, maintain/reduce price, (3) Maturity - sales peak, intense competition, "
            "modify product/market/mix, (4) Decline - sales drop, reduce products/promotions, decide maintain/harvest/drop. "
            "PLC guides strategic decisions throughout product's life."
        ),
        "source": "Chapter 9, Product Life-Cycle Strategies",
    },
    # CHAPTER 10: PRICING
    {
        "id": "Q165",
        "level": "simple",
        "question": "3 major pricing strategies là gì? So sánh starting point và focus của mỗi strategy.",
        "ground_truth": (
            "(1) Customer value-based pricing - start with customer perceptions, set price to match perceived value, then design product to hit target cost. "
            "(2) Cost-based pricing - start with costs, add desired profit margin, results in price. "
            "(3) Competition-based pricing - start with competitor prices, set relative to them. "
            "Best practice: value-based - captures customer value, aligns with marketing concept. Cost-based ignores demand; competition-based ignores differentiation."
        ),
        "source": "Chapter 10, Major Pricing Strategies",
    },
    {
        "id": "Q166",
        "level": "simple",
        "question": "Giải thích 'price-demand relationship'. Tại sao understanding demand curve quan trọng cho pricing decisions?",
        "ground_truth": (
            "Price-demand relationship: thường inverse - higher price = lower demand. Demand curve shows units sold at each price level. "
            "Quan trọng vì: (1) Helps estimate quantity at each price, (2) Reveals price elasticity - sensitivity to changes, "
            "(3) Elastic (luxury) vs inelastic (necessities) demands require different strategies, (4) Affects revenue - lower price không always mean higher revenue, "
            "(5) Many factors affect curve shape. Understanding enables optimizing price cho profit không chỉ volume."
        ),
        "source": "Chapter 10, The Market and Demand",
    },
    # CHAPTER 11: PRICING STRATEGIES
    {
        "id": "Q167",
        "level": "simple",
        "question": "Phân biệt market-skimming pricing và market-penetration pricing. Conditions nào favor mỗi strategy?",
        "ground_truth": (
            "Skimming: set high initial price to 'skim' revenue layer by layer. Favor when: (1) quality/image support high price, "
            "(2) enough buyers want it at high price, (3) costs of small volume not too high, (4) competitors cannot easily enter. "
            "Penetration: set low initial price to penetrate quickly. Favor when: (1) market price-sensitive, "
            "(2) production costs fall với volume, (3) low price helps keep competition out. Opposite approaches với different goals."
        ),
        "source": "Chapter 11, New Product Pricing Strategies",
    },
    {
        "id": "Q168",
        "level": "simple",
        "question": "Product mix pricing strategies gồm những loại nào? Cho ví dụ của product line pricing và captive-product pricing.",
        "ground_truth": (
            "5 strategies: (1) Product line pricing - price steps between line items (TV line từ $199 to $1,999), "
            "(2) Optional-product pricing - accessories/options (xe và options), "
            "(3) Captive-product pricing - products must use with main (razors và blades), "
            "(4) By-product pricing - sell by-products để recover costs (zoo sells manure), "
            "(5) Product bundle pricing - combine products at reduced price (combo meals). Each maximizes value từ product mix."
        ),
        "source": "Chapter 11, Product Mix Pricing Strategies",
    },
    # CHAPTER 12: MARKETING CHANNELS
    {
        "id": "Q169",
        "level": "simple",
        "question": "Marketing channel (distribution channel) là gì? Tại sao companies dùng intermediaries thay vì bán trực tiếp?",
        "ground_truth": (
            "Marketing channel: set of interdependent organizations that help make product available for use/consumption. "
            "Intermediaries vì: (1) Greater efficiency - fewer transactions needed, (2) Economies from contacts/experience/specialization/scale, "
            "(3) Transform assortments (producers→narrow, consumers want→broad), (4) Bridge gaps in time/place/possession. "
            "Intermediaries add value by performing functions producers cannot do as efficiently."
        ),
        "source": "Chapter 12, Supply Chains and the Value Delivery Network",
    },
    {
        "id": "Q170",
        "level": "simple",
        "question": "Vertical Marketing System (VMS) là gì? So sánh 3 types của VMS.",
        "ground_truth": (
            "VMS: channel structure where producers/wholesalers/retailers act as unified system - one owns/contracts/dominates others. "
            "3 types: (1) Corporate VMS - common ownership (Luxottica owns Ray-Ban và Sunglass Hut), "
            "(2) Contractual VMS - contracts coordinate (franchises like McDonald's), "
            "(3) Administered VMS - one member's size/power coordinates (P&G với retailers). "
            "VMS emerged để overcome conventional channel conflicts."
        ),
        "source": "Chapter 12, Vertical Marketing Systems",
    },
    # CHAPTER 13: RETAILING AND WHOLESALING
    {
        "id": "Q171",
        "level": "simple",
        "question": "Retailers phải make những marketing decisions chính nào? Giải thích tầm quan trọng của từng decision.",
        "ground_truth": (
            "Key decisions: (1) Segmentation/targeting/differentiation/positioning - define customer, position store, "
            "(2) Product assortment/services - breadth/depth/quality/exclusivity, (3) Price - high-margin vs high-volume, "
            "(4) Promotion - advertising/PR/social media, (5) Place - location, number of stores. "
            "All must work together để create customer value và differentiate from competitors."
        ),
        "source": "Chapter 13, Retailer Marketing Decisions",
    },
    {
        "id": "Q172",
        "level": "simple",
        "question": "Omni-channel retailing là gì? Tại sao nó critical trong digital age?",
        "ground_truth": (
            "Omni-channel: seamlessly integrate ALL channels (in-store, online, mobile, social) into unified customer experience. "
            "Critical vì: (1) Customers expect consistent experience across channels, (2) Research online, buy anywhere, "
            "(3) Omni-channel customers more valuable (Macy's: 8x value), (4) Compete với pure-play online retailers, "
            "(5) 'Available where and when consumers look for you.' Must blend digital và physical để serve modern shoppers."
        ),
        "source": "Chapter 13, The Need for Omni-Channel Retailing",
    },
    # CHAPTER 14: INTEGRATED MARKETING COMMUNICATIONS
    {
        "id": "Q173",
        "level": "simple",
        "question": "Integrated Marketing Communications (IMC) là gì? Tại sao integration quan trọng?",
        "ground_truth": (
            "IMC: carefully integrating và coordinating company's many communication channels to deliver clear, consistent, "
            "compelling message about organization và products. Quan trọng vì: (1) Consumers không distinguish message sources - merge into single brand message, "
            "(2) Conflicting messages confuse và weaken positioning, (3) Media fragmentation requires coordination, "
            "(4) Every touchpoint is brand contact. IMC ensures unified, consistent communications across all channels."
        ),
        "source": "Chapter 14, The Need for Integrated Marketing Communications",
    },
    {
        "id": "Q174",
        "level": "simple",
        "question": "Promotion mix gồm những tools nào? Briefly describe purpose của mỗi tool.",
        "ground_truth": (
            "5 tools: (1) Advertising - paid, nonpersonal mass media presentation, build awareness/image, "
            "(2) Sales promotion - short-term incentives to encourage purchase/sale, (3) Personal selling - personal interaction, build relationships, "
            "(4) Public relations - build good relations, handle stories, manage reputation, "
            "(5) Direct/digital marketing - direct connections with targeted individuals, interactive. "
            "Each có unique characteristics; optimal blend depends on product/market/objectives."
        ),
        "source": "Chapter 14, The Promotion Mix",
    },
    # CHAPTER 15: ADVERTISING AND PUBLIC RELATIONS
    {
        "id": "Q175",
        "level": "simple",
        "question": "Advertising strategy gồm 2 major elements là gì? Mối quan hệ giữa chúng?",
        "ground_truth": (
            "(1) Creating advertising messages - develop compelling creative content that breaks through clutter, "
            "(2) Selecting advertising media - choose media vehicles to deliver messages. "
            "Relationship: inseparable - message affects media choice, media affects message design. "
            "Must first create good message strategy, then craft executions, then select media to deliver effectively. Both equally important."
        ),
        "source": "Chapter 15, Advertising Strategy",
    },
    {
        "id": "Q176",
        "level": "simple",
        "question": "Public Relations tools (PENCILS) gồm những gì? PR có advantages gì over advertising?",
        "ground_truth": (
            "PR tools: Publications, Events, News, Community involvement, Identity media, Lobbying, Social responsibility. "
            "Advantages over advertising: (1) Higher credibility - editorial seems more 'real', (2) Reach people who avoid ads, "
            "(3) Dramatize company/products effectively, (4) Lower cost, (5) Viral potential through earned media. "
            "Limitations: less control over message, underutilized by many companies."
        ),
        "source": "Chapter 15, Public Relations",
    },
    # CHAPTER 16: PERSONAL SELLING AND SALES PROMOTION
    {
        "id": "Q177",
        "level": "simple",
        "question": "Personal selling process gồm mấy steps? Mô tả ngắn gọn từng step.",
        "ground_truth": (
            "7 steps: (1) Prospecting/qualifying - identify potential customers, "
            "(2) Preapproach - learn about prospect before contact, (3) Approach - meet buyer, start relationship, "
            "(4) Presentation/demonstration - tell product story, show benefits, (5) Handling objections - seek out và address concerns, "
            "(6) Closing - ask for order, (7) Follow-up - ensure satisfaction, build relationship. "
            "Focus on problem-solving, creating value, building relationships."
        ),
        "source": "Chapter 16, The Personal Selling Process",
    },
    {
        "id": "Q178",
        "level": "simple",
        "question": "Sales promotion tools chia thành những categories nào? Cho examples của consumer promotions.",
        "ground_truth": (
            "3 categories: (1) Consumer promotions - pull customers (samples, coupons, rebates, price packs, premiums, contests, POP displays), "
            "(2) Trade promotions - push through channel (discounts, allowances, free goods, push money), "
            "(3) Business promotions - generate leads, stimulate purchases (conventions, trade shows, sales contests). "
            "Consumer promotions most visible - encourage trial, reward loyalty, create urgency."
        ),
        "source": "Chapter 16, Sales Promotion",
    },
    # CHAPTER 17: DIRECT, ONLINE, SOCIAL MEDIA, AND MOBILE MARKETING
    {
        "id": "Q179",
        "level": "simple",
        "question": "Forms of direct và digital marketing gồm những gì? Phân biệt traditional vs digital forms.",
        "ground_truth": (
            "Traditional forms: Direct mail (catalogs, letters), Telephone marketing, Kiosk marketing. "
            "Digital forms: Online marketing (websites, display ads, email), Social media marketing (Facebook, Instagram, Twitter), "
            "Mobile marketing (apps, SMS, location-based). "
            "Digital growing rapidly - offers targeting, personalization, interactivity, measurability. "
            "Traditional still valuable cho certain segments. Best: integrated approach using multiple forms."
        ),
        "source": "Chapter 17, Forms of Direct and Digital Marketing",
    },
    {
        "id": "Q180",
        "level": "simple",
        "question": "Social media marketing advantages và challenges là gì?",
        "ground_truth": (
            "Advantages: (1) Targeted/personal to specific interests, (2) Interactive two-way engagement, "
            "(3) Immediate/timely real-time conversations, (4) Cost-effective reach, (5) Share content, create communities. "
            "Challenges: (1) User-controlled - consumers have power, (2) Hard measure ROI precisely, "
            "(3) Time-consuming to manage well, (4) Negative feedback public/viral, (5) Constantly changing platforms. "
            "Must provide value để engage, không thể force."
        ),
        "source": "Chapter 17, Social Media Marketing",
    },
    # CHAPTER 18: CREATING COMPETITIVE ADVANTAGE
    {
        "id": "Q181",
        "level": "simple",
        "question": "Competitive advantage là gì? Làm thế nào company có thể gain competitive advantage?",
        "ground_truth": (
            "Competitive advantage: advantage over competitors gained by offering greater customer value - lower prices HOẶC more benefits justifying higher prices. "
            "Gain through: (1) Overall cost leadership - lowest production/distribution costs, (2) Differentiation - unique benefits valued by customers, "
            "(3) Focus - serve few segments extremely well. Must deliver on chosen value discipline - operational excellence, product leadership, hoặc customer intimacy."
        ),
        "source": "Chapter 18, Competitive Marketing Strategies",
    },
    {
        "id": "Q182",
        "level": "simple",
        "question": "Competitor analysis gồm những steps nào? Purpose của mỗi step?",
        "ground_truth": (
            "3 steps: (1) Identifying competitors - from both industry view (similar products) và market view (satisfying same needs), "
            "(2) Assessing competitors - objectives/strategies/strengths/weaknesses/reaction patterns, "
            "(3) Selecting competitors to attack/avoid - strong vs weak, close vs distant, good vs bad. "
            "Purpose: understand competitive landscape để design effective strategies, anticipate moves, avoid threats."
        ),
        "source": "Chapter 18, Competitor Analysis",
    },
    # CHAPTER 19: THE GLOBAL MARKETPLACE (though textbook says Chapters 12-20, some editions have 18 main chapters)
    {
        "id": "Q183",
        "level": "simple",
        "question": "Companies quyết định enter international markets như thế nào? Các factors cần xem xét?",
        "ground_truth": (
            "Entry decision factors: (1) Looking at global marketing environment - trade systems, economic environments, political-legal, cultural, "
            "(2) Deciding whether to go international - risks vs benefits, (3) Which markets to enter - potential, risks, infrastructure, competition, "
            "(4) How to enter - exporting, joint venturing, direct investment. "
            "Must balance: market potential vs risks vs resources required vs control desired."
        ),
        "source": "Chapter 19, Deciding Whether to Go Global và Which Markets to Enter",
    },
    {
        "id": "Q184",
        "level": "simple",
        "question": "Standardized vs adapted global marketing - debate và best practice?",
        "ground_truth": (
            "Standardized: same marketing worldwide - economies of scale, consistent global brand. "
            "Adapted: tailored to local markets - meets specific needs, cultural fit. "
            "Debate: global vs local. Best practice: 'think globally, act locally' - standardize core offering/brand essence, "
            "adapt execution/tactics to local preferences. Neither extreme works - balance needed. Key là understanding which elements to standardize vs adapt."
        ),
        "source": "Chapter 19, Deciding on the Global Marketing Program",
    },
    # CHAPTER 20: SUSTAINABLE MARKETING
    {
        "id": "Q185",
        "level": "simple",
        "question": "Sustainable marketing là gì? Khác với traditional marketing concept như thế nào?",
        "ground_truth": (
            "Sustainable marketing: marketing that meets present needs của consumers/businesses/society WITHOUT compromising ability của future generations to meet their needs. "
            "Khác traditional: (1) Long-term not just short-term focus, (2) Considers society not just individual customer, "
            "(3) Includes environmental impact, (4) Ethical considerations embedded. "
            "Triple bottom line: people, planet, profits. Goes beyond customer satisfaction để social responsibility."
        ),
        "source": "Chapter 20, Sustainable Marketing",
    },
    {
        "id": "Q186",
        "level": "simple",
        "question": "5 sustainable marketing principles là gì? Giải thích briefly.",
        "ground_truth": (
            "(1) Consumer-oriented - organize activities around customer needs, "
            "(2) Customer value - put resources vào value-building investments for long-term customer relationships, "
            "(3) Innovative - continuously seek real product/marketing improvements, "
            "(4) Sense-of-mission - define mission in broad social terms, not just product terms, "
            "(5) Societal - balance consumer wants, company requirements, consumer's/society's long-term interests. "
            "Together guide ethical, sustainable marketing practice."
        ),
        "source": "Chapter 20, Sustainable Marketing Principles",
    },
]


def get_questions_by_level(level: str) -> list:
    """Get questions filtered by difficulty level."""
    return [q for q in TEST_QUESTIONS if q["level"] == level]


def get_all_questions() -> list:
    """Get all test questions."""
    return TEST_QUESTIONS


if __name__ == "__main__":
    print(f"Total questions: {len(TEST_QUESTIONS)}")
    print(f"  Simple: {len(get_questions_by_level('simple'))}")
    print(f"  Medium: {len(get_questions_by_level('medium'))}")
    print(f"  Hard: {len(get_questions_by_level('hard'))}")
