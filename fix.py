from lxml import etree
from pathlib import Path

build_xmls = list(Path(".").glob("*_*/build.xml"))

count = 0
for xml in build_xmls:
    # Load the XML file
    tree = etree.parse(xml)
    root = tree.getroot()

    # Add a child element to <path> with id="test.lib"
    path_element = root.find("./path[@id='test.lib']")
    new_child = etree.Element("pathelement", location="${lib.dir}/hamcrest-core-1.3.jar")
    path_element.append(new_child)

    # Add a child element to <classpath> under the specified target
    classpath_element = root.find("./target[@name='evosuite-test']/junit/classpath")
    new_classpath_child = etree.Element("pathelement", path="${build.tests}")
    classpath_element.append(new_classpath_child)

    # Save the modified XML tree back to the file
    tree.write(xml, encoding="utf-8", xml_declaration=True)
    count += 1

print(count, "fixes applied")
