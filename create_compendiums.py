"""Create compendiums by combining the XML

Run this file from the root directory (the place where this file resides)

    $ python create_compendiums.py

This will update the XML files in the Compendiums directory.

"""
from xml.etree import ElementTree
from glob import glob
import argparse

def formatCompendiumFilename(category, version):
    if version == 1:
        return 'Compendiums/{category} Compendium.xml'.format(category=category)
    else:
        return 'Compendiums/{category} Compendium v{version}.xml'.format(category=category, version=version)

class XMLCombiner(object):

    """Combiner for xml files with multiple way to perform the combining"""

    def __init__(self, filenames, version):
        assert len(filenames) > 0, 'No filenames!'
        self.version = version
        self.filenames = filenames

    def combine_pruned(self, output):
        """Combine the xml files and sort the items alphabetically

        Items with the same name are removed.

        :param output: filepath in with the result will be stored.

        """

        itemsDictionary = {}
        duplicates = {}
        chosenVersions = {}
        removedDuplicates = 0

        # Populate the dictionary with items that have a unique name.
        for filename in self.filenames:
        	for element in ElementTree.parse(filename).getroot():
        		name = element.findtext('name')

        		# check whether the item already exists, if so, don't add it but log the filename of the
        		# file which contained the duplicate. If the file existed, add its source file to the chosenVersions
        		if name not in itemsDictionary:
        			itemsDictionary[name] = element
        			chosenVersions[name] = filename
        		else:
        			if duplicates.get(name) == None:
        				duplicates[name] = [filename]
        			else:
        				duplicates[name] = duplicates[name].append(filename)
        			removedDuplicates += 1

        # print the duplicates
        print('Removed total %d duplicate(s)' % removedDuplicates)

        # get the maximum width of the name of an unused item to pad in the next step
        maxDuplicateNameLength = 0;
        maxChosenLength = 0;
        for name in duplicates.keys():
        	if len(name) > maxDuplicateNameLength:
        		maxDuplicateNameLength = len(name)
        	if len(chosenVersions[name]) > maxChosenLength:
        		maxChosenLength = len(chosenVersions[name])

        # print where the duplicates exist
        for name in sorted(duplicates.keys()):
        	print('Found duplicate: %s chosen version: %s ignored: %s' % (name.ljust(maxDuplicateNameLength), 
        																chosenVersions[name].ljust(maxChosenLength),
        																', '.join(duplicates[name])))


        # Create a new XML root node
        outputRoot = ElementTree.Element('compendium', version='5')

        # Alphabetically add the unique elements to the new root node
        for key in sorted(itemsDictionary.keys()):
        	outputRoot.append(self.process_element(itemsDictionary[key]))

        # Create a new tree from the created node and write it
        return ElementTree.ElementTree(outputRoot).write(output, xml_declaration=True, encoding='UTF-8')


    def combine_concatenate(self, output):
        """Combine the xml files by concating the items

        :param output: filepath in with the result will be stored.

        """

        # create root node for the full compendium
        outputRoot = ElementTree.Element('compendium', version='5');
        
        # insert the other files into the full compendium's tag
        for filename in self.filenames:
            outputRoot.extend(ElementTree.parse(filename).getroot().getchildren())

        # write the compendium to the file by creating a new element tree from the root and writing it
        return ElementTree.ElementTree(outputRoot).write(output, encoding='UTF-8')

    def process_element(self, elementToProcess):
        """Takes an XML tag and modifies it so that it fits the specified compendium version.

        :param elementToProcess: the element which shall be processed.
        :param version: the version of the compendium to create
        """

        if self.version == 1:
            for i in range(0, len(elementToProcess)):
                currentElement = elementToProcess[i]

                # check whether this is a source element. If so, replace it with a text element as in the old compendium.
                if currentElement.tag == 'source':
                    placeholder = ElementTree.Element('text')

                    textSourceElement = ElementTree.Element('text')
                    textSourceElement.text = 'Source: %s, page %d' % (currentElement.find('book').text, int(currentElement.find('page').text))

                    elementToProcess[i] = textSourceElement
                    elementToProcess.insert(i, placeholder)

        return elementToProcess


def create_category_compendiums(version):
    """Create the category compendiums

    :return: list of output paths.

    """
    categories = ['Items', 'Character', 'Spells', 'Bestiary']
    output_paths = []
    for category in categories:
        filenames = glob('%s/*.xml' % category)
        output_path = formatCompendiumFilename(category, version)
        output_paths.append(output_path)
        XMLCombiner(filenames, version).combine_pruned(output_path)
    return output_paths


def create_full_compendium(version):
    """Create the category compendiums and combine them into full compendium"""

    category_paths = create_category_compendiums(version)

    full_path = formatCompendiumFilename('Full', version)
    XMLCombiner(category_paths, version).combine_concatenate(full_path)


if __name__ == '__main__':
    print('**** Creating compendium v1 ****')
    create_full_compendium(1)
    print('**** Creating compendium v2 ****')
    create_full_compendium(2)