def chatbot_response(user_input):
    user_input = user_input.lower().strip()
    
    greetings = ["hi", "hello", "hey"]
    farewells = ["bye", "goodbye", "see you", "take care"]
    name_queries = ["what is your name", "who are you", "tell me your name"]
    common_queries = ["how are you", "how's it going", "what's up", "how do you do", "what's new"]
    pricing_queries = ["pricing", "cost", "price", "how much"]
    team_queries = ["team size", "how many people", "employees", "how big is your team"]
    contact_queries = ["contact", "email", "phone", "address", "reach"]
    portfolio_queries = ["portfolio", "projects", "examples", "work", "clients"]
    tech_queries = ["technologies", "tech stack", "tools", "frameworks", "languages"]

    # Handle greetings
    if user_input in greetings:
        return "👋 Hello! Welcome to Appsgenii AI Assistant. How can I assist you today?"
    
    # Handle farewells
    elif user_input in farewells:
        return "😊 Goodbye! Have a great day! Feel free to return anytime."
    
    # Respond to name/identity queries
    elif user_input in name_queries:
        return "🤖 I am Appsgenii's AI Assistant! I'm here to help with information about our services. How can I assist you today?"
    
    # Handle common conversational queries
    elif user_input in common_queries:
        return "😊 I'm doing great, thanks for asking! How can I assist you today?"
    
    # Handle pricing queries
    elif any(keyword in user_input for keyword in pricing_queries):
        return "💵 Our pricing varies based on project requirements. Could you share more details about your project so we can provide an accurate estimate?"
    
    # Handle team size queries
    elif any(keyword in user_input for keyword in team_queries):
        return "👥 We're a growing team of 50+ professionals including developers, designers, and AI experts dedicated to delivering top-quality solutions."
    
    # Handle contact queries
    elif any(keyword in user_input for keyword in contact_queries):
        return "📧 You can reach us at:\n- Email: contact@appsgenii.com\n- Phone: +1 (555) 123-4567\n- Office Hours: Mon-Fri 9AM-5PM EST"
    
    # Handle portfolio queries
    elif any(keyword in user_input for keyword in portfolio_queries):
        return "🖥️ Check out our portfolio: [portfolio.appsgenii.com](https://portfolio.appsgenii.com) featuring 150+ successful projects across various industries!"
    
    # Handle technology queries
    elif any(keyword in user_input for keyword in tech_queries):
        return "🔧 Our core technologies include:\n- AI/ML: TensorFlow, PyTorch\n- Mobile: Flutter, React Native\n- Web: React, Node.js\n- Cloud: AWS, Azure\n- Databases: MongoDB, PostgreSQL"
    
    # Enhanced services response
    elif "services" in user_input or "provide" in user_input:
        return """🌟 **Our Key Services** 🌟
        
        Here's what we offer:
        - 🛠️ Custom Software Development
        - 📱 Mobile App Development (iOS & Android)
        - 🤖 AI & Machine Learning Solutions
        - 🌐 Web Application Development
        - ☁️ Cloud Computing Services
        - 💼 IT Consulting
        
        How can we assist you with these services?"""
    
    # Default fallback
    else:
        return "🤖 I couldn't find a specific answer for that, but I'll check with my team and get back to you! Please feel free to ask anything else. 😊"