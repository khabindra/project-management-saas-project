# १. एउटा सामान्य फङ्सन बनाऔँ जसले निश्चित नाम गरेका आर्गुमेन्टहरू (Arguments) मात्र लिन्छ
def create_project(tenant, user, name, description):
    print("---Data comes here ...---")
    print(f"Tenant: {tenant}")
    print(f"User: {user}")
    print(f"Project Name: {name}")
    print(f"Description: {description}") 
    return "Project created !"


# २. मानौँ यो सिरियलाइजरले प्रमाणित गरेर दिएको सफा डिक्सनरी (Dictionary) हो
validated_data = {
    "name": "E-Commerce Platform",
    "description": "Building an online store"
}

# -------------------------------------------------------------
# परीक्षण १: print() भित्र `**` को प्रयोग (तपाईंको कोडमा एरर आएको लाइन)
# -------------------------------------------------------------
try:
    print("\n--- test  1 started ---")
    # पर्दा पछाडि यो print(name="E-Commerce Platform", description="...") बन्न जान्छ
    print(**validated_data) 
except TypeError as e:
    print(f"crahsed here. Error came: {e}")
    print("reason: print() function doesn't underrstand  'name' र 'description' argument")


# -------------------------------------------------------------
# परीक्षण २: फङ्सन कल गर्दा `**` को प्रयोग (तपाईंको create_project जस्तै)
# -------------------------------------------------------------
print("\n--- Test two started ---")

# यहाँ ** ले डिक्सनरीलाई खोलेर 'name="E-Commerce Platforms"' र 'description="..."' बनाउँछ
# हाम्रो create_project फङ्सनले यी आर्गुमेन्टहरू बुझ्ने हुनाले यो कोड मज्जाले चल्छ!
result = create_project(
    tenant="My-SaaS-Tenant",
    user="ram_user",
    **validated_data 
)

print(f"\nResult: {result}")
