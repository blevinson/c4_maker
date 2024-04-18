import argparse
import os
import inspect
from openai import OpenAI
from dotenv import load_dotenv
import re

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


def generate_annotations(source_code):
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


def workspace_to_dsl(workspace):
    dsl_output = ""

    # Retrieve the first model from the workspace if 'models' is a list or similar collection.
    # This is just an example; you'll need to adjust this based on how the 'models' are actually stored or accessed.
    model = workspace.models[0]

    # Convert model.elements dictionary to a list of tuples (name, element)
    elements_data = [(name, element) for name, element in model.elements.items()]

    # Iterate through the elements data list
    for name, element in elements_data:
        dsl_output += f"element {name} {{\n"
        dsl_output += f"  description {element.description}\n"
        # Add other properties and relationships as needed
        dsl_output += "}\n"

    # Return the DSL representation as a string
    return dsl_output


from pystructurizr.dsl import Workspace, Model, Component, Container, Person, SoftwareSystem


def generate_structurizr_dsl(elements, relationships):
    workspace = Workspace()
    model = Model(name='Application')
    workspace.models.append(model)

    main_system = SoftwareSystem(name="Main System", description="Main system handling all operations")
    model.elements.append(main_system)

    main_container = Container(name="Main Container", description="Primary container for all components")
    main_system.elements.append(main_container)

    # Create components and add to the main container
    for el_name, el_func in elements.items():
        el_details = el_func.c4_details
        component = Component(name=el_name, description=el_details['description'], technology=el_details.get('technology', 'Python'))
        main_container.elements.append(component)

    # Assuming relationships need to be added here; adjust as necessary
    for rel in relationships:
        source = next((comp for comp in main_container.elements if comp.name == rel['source']), None)
        target = next((comp for comp in main_container.elements if comp.name == rel['target']), None)
        if source and target:
            source.uses(target, description=rel.get('description', ''), technology=rel.get('technology', ''))

    return workspace


# Example usage:
# elements = {
#     'calculate_trade_amount': lambda: {'type': 'Component', 'description': 'Calculates the amount for trading a token', 'technology': 'Python'},
#     # Add more elements as needed
# }
#
# relationships = [
#     {'source': 'calculate_trade_amount', 'target': 'fetch_market_data', 'description': 'Calculates trade amounts based on market data'}
#     # Define more relationships as needed
# ]
#
# # workspace = generate_structurizr_dsl(elements, relationships)
# # print(workspace)





def sanitize_identifier(name):
    # Replace spaces with underscores and remove disallowed characters
    sanitized = re.sub('[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))
    return sanitized


def setup_workspace():
    workspace = Workspace()

    # Create elements
    user = Person("User", "A user of my software system.")
    software_system = SoftwareSystem("Main Software System", "My software system.")

    # Create a model and add elements to it
    model = workspace.Model(name="My Model")
    model.Person(user)
    model.SoftwareSystem(software_system)

    # Define relationships
    # user.uses(software_system.name, "Uses")

    # Optionally handle views
    # system_context_view = workspace.SystemContextView(software_system, "SystemContext",
    #                                                   "An example System Context view for the software system.")
    # system_context_view.include(user)
    # system_context_view.include(software_system)
    # system_context_view.autoLayout()

    # Define styles
    # workspace.Styles(
    #     {"tag": "Software System", "background": "#1168bd", "color": "#ffffff"},
    #     {"tag": "Person", "shape": "Person", "background": "#08427b", "color": "#ffffff"}
    # )
    # workspace.models.append(model)
    # Generate DSL from the workspace
    return workspace.dump()


# dsl_output = setup_workspace()
# print(dsl_output)
# Example Usage
# software_system = SoftwareSystem("Software System", "My software system.")
# dsl_output = setup_workspace()
# print(dsl_output)


# Example Usage
# dsl_output = setup_workspace()

# print(dsl_output)


# You would call this method with the elements and relationships you've defined elsewhere


def main():
    # Example Usage
    # dsl_output = setup_workspace()
    # print(dsl_output)
    # dsl_filename = f'/Users/brant/structurizr/workspace.dsl'
    # with open(dsl_filename, 'w') as file:
    #     file.write(str(dsl_output))
    # print(f"Structurizr DSL diagram written to {dsl_filename}")
    parser = argparse.ArgumentParser(description="Generate architecture diagrams from Python code.")
    parser.add_argument('filename', type=str, help='The Python file to analyze.')
    parser.add_argument('--generate-annotations', action='store_true', help='Generate annotations for the code.')
    parser.add_argument('--generate-plantuml', action='store_true', help='Generate a PlantUML diagram.')
    parser.add_argument('--generate-structurizr', action='store_true', help='Generate a Structurizr DSL diagram.')
    args = parser.parse_args()

    # Validate the file extension
    if not args.filename.endswith('.py'):
        print("Error: The file must be a Python '.py' file.")
        return

    module_name = args.filename.rstrip('.py')

    # Attempt to import the module
    try:
        module = __import__(module_name)
    except ModuleNotFoundError:
        print(f"Error: No module named '{module_name}' found.")
        return

    elements, relationships = None, None  # Initialize these to None to handle possible checks later

    if args.generate_annotations:
        source_code = inspect.getsource(module)
        generate_annotations(source_code)

    # Check if any diagram generation is requested
    if args.generate_plantuml or args.generate_structurizr:
        # Prepare elements and relationships for diagram generation
        elements = {name: obj for name, obj in inspect.getmembers(module) if hasattr(obj, 'c4_details')}
        relationships = [rel for _, obj in inspect.getmembers(module) for rel in getattr(obj, 'c4_relationships', [])]

    if args.generate_plantuml:
        print("Generating PlantUML diagram...")
        plantuml_code = generate_plantuml(elements, relationships)
        output_filename = f'{module_name}_diagram.puml'
        with open(output_filename, 'w') as file:
            file.write(plantuml_code)
        print(f"PlantUML diagram written to {output_filename}")

    if args.generate_structurizr:
        print("Generating Structurizr DSL diagram...")
        structurizr_dsl = generate_structurizr_dsl(elements, relationships)
        # dsl_filename = f'{module_name}_structurizr.dsl'
        dsl_filename = '/Users/brant/structurizr/workspace.dsl'
        with open(dsl_filename, 'w') as file:
            file.write(str(structurizr_dsl.dump()))
        print(f"Structurizr DSL diagram written to {dsl_filename}")

    if not (args.generate_plantuml or args.generate_structurizr or args.generate_annotations):
        print("No output format specified. Use --generate-plantuml or --generate-structurizr to generate diagrams.")
        return


if __name__ == "__main__":
    main()
