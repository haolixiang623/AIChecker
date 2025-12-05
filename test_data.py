from data.storage import StorageManager
from data.models import ScanSession, PageElement

def main():
    print("Initializing StorageManager...")
    storage = StorageManager()
    
    print("Creating test session...")
    session = storage.create_session("https://example.com")
    print(f"Session created: ID={session.id}, URL={session.url}, Status={session.status}")
    
    print("Saving test elements...")
    elements_data = [
        {"type": "a", "text": "Link 1", "href": "/link1", "selector": "a.link1"},
        {"type": "button", "text": "Button 1", "selector": "button#btn1"}
    ]
    storage.save_elements(session.id, elements_data)
    
    print("Retrieving elements...")
    saved_elements = storage.get_elements_by_session(session.id)
    print(f"Found {len(saved_elements)} elements.")
    for el in saved_elements:
        print(f"- {el.type}: {el.text}")
        
    print("Completing session...")
    storage.complete_session(session.id)
    updated_session = ScanSession.get_by_id(session.id)
    print(f"Session status: {updated_session.status}, End Time: {updated_session.end_time}")

if __name__ == "__main__":
    main()
