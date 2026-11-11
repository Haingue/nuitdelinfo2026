"""
Tests pour la détection des projets
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from quality_factory.detect import detect_all_projects
from quality_factory.detect.python import detect_python_projects
from quality_factory.detect.java import detect_java_projects
from quality_factory.detect.node import detect_node_projects


@pytest.fixture
def temp_workspace():
    """Crée un workspace temporaire"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestPythonDetection:
    """Tests pour la détection des projets Python"""
    
    def test_detect_python_with_test_files(self, temp_workspace):
        """Test la détection d'un projet Python avec des fichiers de test"""
        # Créer un projet Python simple
        project_dir = temp_workspace / "my_python_project"
        project_dir.mkdir()
        
        # Créer un fichier de test
        test_file = project_dir / "test_example.py"
        test_file.write_text("def test_example():\n    assert True\n")
        
        # Créer un fichier de configuration
        setup_file = project_dir / "setup.py"
        setup_file.write_text("from setuptools import setup\nsetup(name='test')\n")
        
        # Détecter
        projects = detect_python_projects(temp_workspace)
        
        assert len(projects) == 1
        assert projects[0].path == project_dir
    
    def test_detect_python_without_test_files(self, temp_workspace):
        """Test la détection d'un projet Python sans fichiers de test"""
        # Créer un projet Python sans tests
        project_dir = temp_workspace / "no_tests_project"
        project_dir.mkdir()
        
        # Créer un fichier Python normal
        main_file = project_dir / "main.py"
        main_file.write_text("def main():\n    pass\n")
        
        # Créer un fichier de configuration
        setup_file = project_dir / "setup.py"
        setup_file.write_text("from setuptools import setup\nsetup(name='test')\n")
        
        # Détecter
        projects = detect_python_projects(temp_workspace)
        
        # Aucun projet ne devrait être détecté (pas de fichiers de test)
        assert len(projects) == 0


class TestJavaDetection:
    """Tests pour la détection des projets Java"""
    
    def test_detect_maven_project(self, temp_workspace):
        """Test la détection d'un projet Maven"""
        # Créer un projet Maven simple
        project_dir = temp_workspace / "maven_project"
        project_dir.mkdir()
        
        # Créer un pom.xml
        pom_file = project_dir / "pom.xml"
        pom_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project>
    <groupId>com.example</groupId>
    <artifactId>test</artifactId>
    <version>1.0</version>
</project>""")
        
        # Créer un test Java
        test_dir = project_dir / "src" / "test" / "java" / "com" / "example"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "ExampleTest.java"
        test_file.write_text("public class ExampleTest {}//")
        
        # Détecter
        projects = detect_java_projects(temp_workspace)
        
        assert len(projects) == 1
        assert projects[0].path == project_dir
        assert projects[0].build_tool.value == "maven"
    
    def test_detect_gradle_project(self, temp_workspace):
        """Test la détection d'un projet Gradle"""
        # Créer un projet Gradle simple
        project_dir = temp_workspace / "gradle_project"
        project_dir.mkdir()
        
        # Créer un build.gradle
        build_file = project_dir / "build.gradle"
        build_file.write_text("plugins { id 'java' }//")
        
        # Créer un test Java
        test_dir = project_dir / "src" / "test" / "java"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "ExampleTest.java"
        test_file.write_text("public class ExampleTest {}//")
        
        # Détecter
        projects = detect_java_projects(temp_workspace)
        
        assert len(projects) == 1
        assert projects[0].path == project_dir
        assert projects[0].build_tool.value == "gradle"


class TestNodeDetection:
    """Tests pour la détection des projets Node.js"""
    
    def test_detect_node_with_test_script(self, temp_workspace):
        """Test la détection d'un projet Node avec un script test"""
        # Créer un projet Node simple
        project_dir = temp_workspace / "node_project"
        project_dir.mkdir()
        
        # Créer un package.json avec un script test
        package_file = project_dir / "package.json"
        package_file.write_text('''{
    "name": "test",
    "scripts": {
        "test": "echo test"
    }
}''')
        
        # Détecter
        projects = detect_node_projects(temp_workspace)
        
        assert len(projects) == 1
        assert projects[0].path == project_dir
    
    def test_detect_node_without_test_script(self, temp_workspace):
        """Test la détection d'un projet Node sans script test"""
        # Créer un projet Node sans script test
        project_dir = temp_workspace / "no_test_node"
        project_dir.mkdir()
        
        # Créer un package.json sans script test
        package_file = project_dir / "package.json"
        package_file.write_text('''{
    "name": "test"
}''')
        
        # Détecter
        projects = detect_node_projects(temp_workspace)
        
        # Aucun projet ne devrait être détecté
        assert len(projects) == 0


class TestAllDetection:
    """Tests pour la détection globale"""
    
    def test_detect_all_projects(self, temp_workspace):
        """Test la détection de tous les types de projets"""
        # Créer un projet Python
        python_dir = temp_workspace / "python_project"
        python_dir.mkdir()
        (python_dir / "test_foo.py").write_text("def test_foo(): pass")
        (python_dir / "setup.py").write_text("from setuptools import setup\nsetup(name='test')")
        
        # Créer un projet Maven
        maven_dir = temp_workspace / "maven_project"
        maven_dir.mkdir()
        (maven_dir / "pom.xml").write_text("<?xml version='1.0'?><project><groupId>test</groupId></project>")
        test_dir = maven_dir / "src" / "test" / "java"
        test_dir.mkdir(parents=True)
        (test_dir / "Test.java").write_text("public class Test {}")
        
        # Créer un projet Node
        node_dir = temp_workspace / "node_project"
        node_dir.mkdir()
        (node_dir / "package.json").write_text('{"scripts": {"test": "echo test"}}')
        
        # Détecter
        result = detect_all_projects(temp_workspace)
        
        assert len(result.python_projects) == 1
        assert len(result.java_projects) == 1
        assert len(result.node_packages) == 1
        assert len(result.all_projects) == 3
