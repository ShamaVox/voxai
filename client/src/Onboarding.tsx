import React, { FC, useState, useContext, useEffect, useMemo } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, ScrollView } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import * as DocumentPicker from 'expo-document-picker';
import styles from './styles/OnboardingStyles';
import axios from 'axios';
import { SERVER_ENDPOINT } from './utils/Axios';
import { AuthContext } from './AuthContext';

type SkillKey = 'hard' | 'soft' | 'behavioral';

interface Skill {
  skill_id: string;
  skill_name: string;
  type?: 'hard' | 'soft' | 'behavioral';
}

interface FormData {
  jobDescriptionFile: DocumentPicker.DocumentPickerAsset[] | null;
  companyWebsite: string;
  companySize: string;
  hiringDocument: DocumentPicker.DocumentPickerAsset[] | null;
  jobTitle: string;
  positionType: string;
  department: string;
  jobSummary: string;
  responsibilities: string;
  jobRequirements: string;
  hardSkills: Skill[];
  softSkills: Skill[];
  behavioralSkills: Skill[];
  interviewOption: string;
}

const Onboarding: FC = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const { finishOnboarding } = useContext(AuthContext);
  const [formData, setFormData] = useState<FormData>({
    jobDescriptionFile: null,
    companyWebsite: '',
    companySize: '',
    hiringDocument: null,
    jobTitle: '',
    positionType: '',
    department: '',
    jobSummary: '',
    responsibilities: '',
    jobRequirements: '',
    hardSkills: [],
    softSkills: [],
    behavioralSkills: [],
    interviewOption: '',
  });

  const [allSkills, setAllSkills] = useState<Skill[]>([]);
  const [currentSkillInput, setCurrentSkillInput] = useState('');
  const [currentSkillType, setCurrentSkillType] = useState<'hard' | 'soft' | 'behavioral' | null>(null);

  useEffect(() => {
    fetchAllSkills();
  }, []);

  const fetchAllSkills = async () => {
    try {
      const response = await axios.get(SERVER_ENDPOINT('skills'));
      setAllSkills(response.data.skills); 
    } catch (error) {
      console.error('Error fetching skills:', error);
    }
  };

  const skillSuggestions = useMemo(() => {
    if (currentSkillInput.length > 1 && currentSkillType && Array.isArray(allSkills)) {
      return allSkills.filter(skill => 
        skill.type === currentSkillType &&
        skill.skill_name.toLowerCase().includes(currentSkillInput.toLowerCase())
      );
    }
    return [];
  }, [currentSkillInput, currentSkillType, allSkills]);


  const handleSkillInputChange = (text: string, type: 'hard' | 'soft' | 'behavioral') => {
    setCurrentSkillInput(text);
    setCurrentSkillType(type);
  };

  const addSkill = (skill: Skill) => {
    const skillType = `${skill.type}Skills` as SkillKey;
    if (!formData[skillType].some(s => s.skill_id === skill.skill_id)) {
      setFormData(prevData => ({
        ...prevData,
        [skillType]: [...prevData[skillType], skill]
      }));
    }
    setCurrentSkillInput('');
    setCurrentSkillType(null);
  };

  const removeSkill = (skillToRemove: Skill, type: SkillKey) => {
    setFormData(prevData => ({
      ...prevData,
      [type]: prevData[type].filter(skill => skill.skill_id !== skillToRemove.skill_id)
    }));
  };

  const handleNextPage = async () => {
    if (currentPage < 4) {
      if (validatePage()) {
        setCurrentPage(currentPage + 1);
      } else {
        // TODO: Display error on the page
        console.error('Please fill in all required fields.');
      }
    } else {
      try {
        const response = await axios.post(SERVER_ENDPOINT('onboarding'), formData);
        if (response.status === 200 && response.data.success) {
          console.log('Submission successful');
          finishOnboarding(); // Call finishOnboarding to update the auth state
        } else {
          console.error('Submission failed');
        }
      } catch (error) {
        console.error('An error occurred during submission', error);
      }
    }
  };

  const validatePage = () => {
    // Implement validation for required fields on each page
    switch (currentPage) {
      case 1:
        return formData.jobDescriptionFile && formData.companyWebsite && formData.companySize && formData.hiringDocument;
      case 2:
        return formData.jobTitle && formData.positionType && formData.department &&
               formData.jobSummary && formData.responsibilities && formData.jobRequirements;
      case 3:
        return formData.hardSkills.length > 0 && formData.softSkills.length > 0 && formData.behavioralSkills.length > 0;
      case 4:
        return formData.interviewOption;
      default:
        return false;
    }
  };

  const handleInputChange = (name: string, value: string) => {
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleFileChange = async (name: 'jobDescriptionFile' | 'hiringDocument') => {
    try {
      const result = await DocumentPicker.getDocumentAsync({ type: '*/*', multiple: false });
      if (!result.canceled) {
        setFormData(prevData => ({
          ...prevData,
          [name]: result.assets
        }));
      }
    } catch (error) {
      console.error('Error picking document:', error);
    }
  };

  const renderPaginationCircle = (page: number) => (
    <View style={[styles.circle, currentPage === page ? styles.activeCircle : styles.inactiveCircle]}>
      <Text style={styles.circleText}>{page}</Text>
    </View>
  );

  const handleConnectCalendar = (calendarType: string) => {
    // TODO: Use Okta to sync with Google Calendar if the option is available
    // const { okta } = useContext(AuthContext);
    // if (okta) {
    //   // Make an API request to Okta to get Google Calendar token
    //   // User may need to log in again to Okta 
    // }
    // else {
      // Open a Google sign in tab 
      // Request Google Calendar permissions 
      // Get the token 
    // }
    return; 
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.paginationContainer}>
        {[1, 2, 3, 4].map((page) => (
          <React.Fragment key={page}>
            {renderPaginationCircle(page)}
            {page < 4 && <View style={styles.line} />}
          </React.Fragment>
        ))}
      </View>

      {currentPage === 1 && (
        <View>
          <Text>Job Description (Upload File)</Text>
          <TouchableOpacity style={styles.uploadButton} onPress={() => handleFileChange('jobDescriptionFile')}>
            <Text>{formData.jobDescriptionFile ? 'File selected' : 'Select file'}</Text>
          </TouchableOpacity>
          
          <Text>Company Website</Text>
          <TextInput
            style={styles.input}
            value={formData.companyWebsite}
            onChangeText={(text) => handleInputChange('companyWebsite', text)}
          />
          
          <Text>Company Size</Text>
          <TextInput
            style={styles.input}
            value={formData.companySize}
            onChangeText={(text) => handleInputChange('companySize', text)}
          />
          
          <Text>Hiring Document (Upload File)</Text>
          <TouchableOpacity style={styles.uploadButton} onPress={() => handleFileChange('hiringDocument')}>
            <Text>{formData.hiringDocument ? 'File selected' : 'Select file'}</Text>
          </TouchableOpacity>
        </View>
      )}

      {currentPage === 2 && (
        <View style={styles.twoColumnLayout}>
          <View style={styles.leftColumn}>
            <Text>Job Title</Text>
            <TextInput
              style={styles.input}
              value={formData.jobTitle}
              onChangeText={(text) => handleInputChange('jobTitle', text)}
            />
            
            <Text>Position Type</Text>
            <TextInput
              style={styles.input}
              value={formData.positionType}
              onChangeText={(text) => handleInputChange('positionType', text)}
            />
            
            <Text>Department</Text>
            <TextInput
              style={styles.input}
              value={formData.department}
              onChangeText={(text) => handleInputChange('department', text)}
            />
            
            <Text>Job Summary</Text>
            <TextInput
              style={styles.textArea}
              value={formData.jobSummary}
              onChangeText={(text) => handleInputChange('jobSummary', text)}
              multiline
            />
            
            <Text>Responsibilities</Text>
            <TextInput
              style={styles.textArea}
              value={formData.responsibilities}
              onChangeText={(text) => handleInputChange('responsibilities', text)}
              multiline
            />
            
            <Text>Job Requirements</Text>
            <TextInput
              style={styles.textArea}
              value={formData.jobRequirements}
              onChangeText={(text) => handleInputChange('jobRequirements', text)}
              multiline
            />
          </View>
          
          <View style={styles.rightColumn}>
            {(['hard', 'soft', 'behavioral'] as const).map(skillType => (
              <View key={skillType}>
                <Text>{skillType.charAt(0).toUpperCase() + skillType.slice(1)} Skills</Text>
                <TextInput
                  style={styles.input}
                  value={currentSkillType === skillType ? currentSkillInput : ''}
                  onChangeText={(text) => handleSkillInputChange(text, skillType)}
                  onSubmitEditing={() => {
                    if (skillSuggestions.length > 0) {
                      addSkill(skillSuggestions[0]);
                    }
                  }}
                />
                {currentSkillType === skillType && skillSuggestions.length > 0 && (
                  <FlatList
                    style={styles.suggestionList}
                    data={skillSuggestions}
                    renderItem={({ item }) => (
                      <TouchableOpacity
                        style={styles.suggestionItem}
                        onPress={() => addSkill(item)}
                      >
                        <Text>{item.skill_name}</Text>
                      </TouchableOpacity>
                    )}
                    keyExtractor={(item) => item.skill_id}
                  />
                )}
                <View style={styles.skillTags}>
                  {formData[`${skillType}Skills` as SkillKey].map(skill => (
                    <View key={skill.skill_id} style={styles.skillTag}>
                      <Text style={styles.skillTagText}>{skill.skill_name}</Text>
                      <TouchableOpacity onPress={() => removeSkill(skill, `${skillType}Skills` as SkillKey)}>
                        <Text style={styles.removeSkillButton}>×</Text>
                      </TouchableOpacity>
                    </View>
                  ))}
                </View>
              </View>
            ))}
          </View>
        </View>
      )}

      {currentPage === 3 && (
        <View>
          <Text>Connect Your Calendars</Text>
          <TouchableOpacity
            style={styles.button}
            onPress={() => handleConnectCalendar('Google')}
          >
            <Text style={styles.buttonText}>Connect Google Calendar</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.button}
            onPress={() => handleConnectCalendar('Calendly')}
          >
            <Text style={styles.buttonText}>Connect Calendly</Text>
          </TouchableOpacity>
        </View>
      )}

      <TouchableOpacity
        style={styles.button}
        onPress={handleNextPage}
      >
        <Text style={styles.buttonText}>
          {currentPage < 3 ? 'Next page' : 'Submit'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

export default Onboarding;