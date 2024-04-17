import re
import sys
import os
import inspect
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables and initialize the OpenAI client
load_dotenv("../.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

shot_1 = """
    @startuml
    !include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml
    title Component diagram for Internet Banking System - API Application
    Component("bot", "Bot", "Python", "Represents the trading bot")
    Component("bot_control_component", "Bot Control", "Python", "Controls the execution of the trading bot and scheduling")
    Component("data_retrieval_component", "Data Retrieval", "Python", "Responsible for fetching data from external APIs or blockchain")
    Component("scheduled_bot", "Scheduled Bot", "Python", "Represents the scheduled bot")
    Component("trading_operations_component", "Trading Operations", "Python", "Handles trading operations such as fetching position, opening and closing positions")
    Rel("bot_control_component", "bot", "Executes", "Component")
    Rel("bot_control_component", "scheduled_bot", "Schedules", "Component")
    Rel("bot_control_component", "data_retrieval_component", "Uses", "Component")
    Rel("trading_operations_component", "data_retrieval_component", "Uses", "Component")
    Rel("bot_control_component", "trading_operations_component", "Uses", "Component")
    @enduml
    """
shot_2 = """
    @c4_element('Component', label="Data Retrieval", technology="Python",
                description="Responsible for fetching data from external APIs or blockchain")
    def data_retrieval_component():
        pass
    
    # Trading Operations Component
    @c4_element('Component', label="Trading Operations", technology="Python",
                description="Handles trading operations such as fetching position, opening and closing positions")
    def trading_operations_component():
        pass
    
    # Bot Control Component
    @c4_element('Component', label="Bot Control", technology="Python",
                description="Controls the execution of the trading bot and scheduling")
    def bot_control_component():
        pass
    
    # Bot Component
    @c4_element('Component', label="Bot", technology="Python",
                description="Represents the trading bot")
    def bot():
        pass
    
    # Scheduled Bot Component
    @c4_element('Component', label="Scheduled Bot", technology="Python",
                description="Represents the scheduled bot")
    def scheduled_bot():
        pass
    
    # Relationships
    @c4_relationship('bot_control_component', 'data_retrieval_component', "Uses", "Component")
    def uses_relationship1():
        pass
    
    @c4_relationship('trading_operations_component', 'data_retrieval_component', "Uses", "Component")
    def uses_relationship2():
        pass
    
    @c4_relationship('bot_control_component', 'trading_operations_component', "Uses", "Component")
    def uses_relationship3():
        pass
    
    @c4_relationship('bot_control_component', 'bot', "Executes", "Component")
    def executes_relationship1():
        pass
    
    @c4_relationship('bot_control_component', 'scheduled_bot', "Schedules", "Component")
    def schedules_relationship1():
        pass
    """


def estimate_tokens(text):
    """ Roughly estimate the number of tokens in the text based on whitespace. """
    return len(text.split())


def split_text_into_chunks(text, max_chunk_size=3000):
    """ Splits the text into manageable chunks according to the token limit. """
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if estimate_tokens(' '.join(current_chunk + [word])) > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def generate_annotation(source_code):
    """Generates annotations for a given source code using OpenAI's API, handling large inputs by splitting them into chunks."""
    responses = []
    prompt = (
        f"Do not add comments. Examine code and figure out Components and the relationships between them. Look at {shot_2} as a reference to add decorators. Use @c4_relationship for relationships and @c4_element for components. DO A STEP BY STEP ANALYSIS AND FIGURE OUT RELATIONSHIPS BETWEEN COMPONENTS. ADD THE DECORATORS TO THIS CODE {source_code}. DO NOT CHANGE ANYTHING OTHER THEN ADDING DOCORATORS."
        f"Here is the example plantuml code that is being created: {shot_1}")
    chunks = split_text_into_chunks(prompt)

    for chunk in chunks:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "YOU ONLY RESPOND IN CODE WITH NO OTHER COMMENTS. FIGURE OUT THE "
                                              "RELATIONSHIPS BETWEEN COMPONENTS. Add 'pass' after each method so it "
                                              "doesn't cause errors."},
                {"role": "user", "content": chunk}
            ]
        )
        responses.append(response.choices[0].message.content.strip())

    return " ".join(responses)

def check_missing_relationships(elements, relationships):
    defined_components = set(elements.keys())
    referenced_components = set()

    for rel in relationships:
        referenced_components.add(rel['source'])
        referenced_components.add(rel['target'])

    missing_components = referenced_components - defined_components
    if missing_components:
        print("Missing component definitions for:")
        for component in missing_components:
            print(component)
    else:
        print("No missing components.")

def c4_element(type_, **kwargs):
    def decorator(func):
        if not hasattr(func, 'c4_details'):
            func.c4_details = {}
        func.c4_details['type'] = type_
        func.c4_details.update(kwargs)
        return func

    return decorator


def c4_relationship(source, target, description, technology=""):
    def decorator(func):
        if not hasattr(func, 'c4_relationships'):
            func.c4_relationships = []
        func.c4_relationships.append(
            {'source': source, 'target': target, 'description': description, 'technology': technology})
        return func

    return decorator


def generate_plantuml(elements, relationships):
    lines = [
        '@startuml',
        '!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml',
        'title Component diagram for application'
    ]
    check_missing_relationships(elements, relationships)
    for el in elements.values():
        lines.append(
            f'Component("{el.__name__}", "{el.c4_details["label"]}", "{el.c4_details["technology"]}", "{el.c4_details["description"]}")')
    for rel in relationships:
        lines.append(f'Rel("{rel["source"]}", "{rel["target"]}", "{rel["description"]}", "{rel["technology"]}")')
    lines.append('@enduml')
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <module_name.py> [--generate]")
        return

    module_file = sys.argv[1]
    generate_annotations = '--generate' in sys.argv

    if not module_file.endswith('.py'):
        print("Error: The file must be a Python '.py' file.")
        return

    module_name = module_file.rstrip('.py')

    try:
        module = __import__(module_name)
    except ModuleNotFoundError:
        print(f"Error: No module named '{module_name}' found.")
        return

    source_code = inspect.getsource(module)

    if generate_annotations:
        print("Generating annotations...")
        annotation_suggestions = generate_annotation(source_code)
        # print("Annotations generated:")
        # print(annotation_suggestions)
        imports = ("from c4_maker import c4_element, c4_relationship\n"
                   "import os\n"
                   "from dotenv import load_dotenv\n"
                   )
        # code_to_write = imports + "\n".join(extract_code_from_text(annotation_suggestions))
        code_to_write = imports + "\n" + annotation_suggestions
        # code_to_write = annotation_suggestions

        print(f"Generated code:\n{code_to_write}")
        new_filename = f"{module_name}_update.py"
        with open(new_filename, 'w') as file:
            file.write(code_to_write)
            print(f"Updated code written to {new_filename}")
    else:
        print("Generating PlantUML diagram...")
        elements = {name: obj for name, obj in inspect.getmembers(module) if hasattr(obj, 'c4_details')}
        relationships = [rel for _, obj in inspect.getmembers(module) for rel in getattr(obj, 'c4_relationships', [])]
        plantuml_code = generate_plantuml(elements, relationships)
        output_filename = f'{module_name}_diagram.puml'
        with open(output_filename, 'w') as file:
            file.write(plantuml_code)
        print(f"PlantUML diagram written to {output_filename}")


if __name__ == "__main__":
    main()
