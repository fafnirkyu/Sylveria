from assistant.core import PersonalAssistant

if __name__ == "__main__":
    assistant = PersonalAssistant()
    try:
        assistant.gui.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        assistant.save_memory()  # Save memory when closing 