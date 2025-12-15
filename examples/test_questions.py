"""
Marketing Knowledge Test Questions

Curated questions for testing marketing knowledge retrieval and reasoning.
These questions focus on conceptual understanding and problem-solving,
NOT specific case studies or company examples.

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
