import React, { FC, useState, useContext, useEffect, useMemo } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, ScrollView, Modal } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import * as DocumentPicker from 'expo-document-picker';
import styles from './styles/OnboardingStyles';
import errorStyles from './styles/ErrorStyles';
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
  companyName: string;
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
}

interface FormErrors {
  jobDescriptionFile?: string;
  companyWebsite?: string;
  companySize?: string;
  hiringDocument?: string;
  jobTitle?: string;
  positionType?: string;
  department?: string;
  jobSummary?: string;
  responsibilities?: string;
  jobRequirements?: string;
  hardSkills?: string;
  softSkills?: string;
  behavioralSkills?: string;
  submission?: string;
}

const ErrorModal: FC<{ visible: boolean; errors: string[]; onClose: () => void }> = ({ visible, errors, onClose }) => (
  <Modal
    animationType="fade"
    transparent={true}
    visible={visible}
    onRequestClose={onClose}
  >
    <View style={errorStyles.centeredView}>
      <View style={errorStyles.modalView}>
        <Text style={errorStyles.modalTitle}>Please correct the following errors:</Text>
        {errors.map((error, index) => (
          <Text key={index} style={errorStyles.modalText}>• {error}</Text>
        ))}
        <TouchableOpacity
          style={[errorStyles.button, errorStyles.buttonClose]}
          onPress={onClose}
        >
          <Text style={errorStyles.textStyle}>Close</Text>
        </TouchableOpacity>
      </View>
    </View>
  </Modal>
);

const Onboarding: FC = () => {
  const { okta } = useContext(AuthContext);
  const [currentPage, setCurrentPage] = useState(1);
  const { finishOnboarding } = useContext(AuthContext);
  const [formData, setFormData] = useState<FormData>({
    jobDescriptionFile: null,
    companyName: '',
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
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [showErrorModal, setShowErrorModal] = useState(false);

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

  const validatePage = (): boolean => {
    const fieldsToValidate: (keyof FormData)[] = 
      currentPage === 1 ? ['jobDescriptionFile', 'companyName', 'companyWebsite', 'companySize', 'hiringDocument'] :
      currentPage === 2 ? ['jobTitle', 'positionType', 'department', 'jobSummary', 'responsibilities', 'jobRequirements', 'hardSkills', 'softSkills', 'behavioralSkills'] :
      currentPage === 3 ? [] : [];

    const newErrors: FormErrors = {};
    fieldsToValidate.forEach(field => {
      const error = validateField(field, formData[field]);
      if (error) {
        newErrors[field] = error;
      }
    });

    setFormErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextPage = async () => {
    if (validatePage()) {
      if (currentPage < 3) {
        setCurrentPage(currentPage + 1);
      } else {
        try {
          const response = await axios.post(SERVER_ENDPOINT('onboarding'), formData);
          if (response.status === 200 && response.data.success) {
            console.log('Submission successful');
            finishOnboarding();
          } else {
            throw new Error('Submission failed');
          }
        } catch (error) {
          console.error('An error occurred during submission', error);
          setFormErrors({ ...formErrors, submission: 'An error occurred while submitting the form. Please try again.' });
          setShowErrorModal(true);
        }
      }
    } else {
      setShowErrorModal(true);
    }
  };

  const validateField = (field: keyof FormData, value: any): string | undefined => {
    switch (field) {
      case 'companyName':
          return (value || !okta) ? undefined : `${field} is required`;
      case 'jobDescriptionFile':
      case 'hiringDocument':
        return value ? undefined : `${field} is required`;
      case 'companyWebsite':
        return value ? 
          (/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/.test(value) ? 
            undefined : 'Invalid website URL') : 
          'Company website is required';
      case 'companySize':
        if (!value) return 'Company size is required';
        if (isNaN(Number(value))) return 'Company size must be a number';
        return undefined;
      case 'jobTitle':
      case 'positionType':
      case 'department':
      case 'jobSummary':
      case 'responsibilities':
      case 'jobRequirements':
        return value ? undefined : `${field} is required`; // TODO: Print this as 'Job Requirements' instead of 'jobRequirements'
      case 'hardSkills':
      case 'softSkills':
      case 'behavioralSkills':
        return (value as Skill[]).length > 0 ? undefined : `At least one ${field} is required`;
      default:
        return undefined;
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
        {[1, 2, 3].map((page) => (
          <React.Fragment key={page}>
            {renderPaginationCircle(page)}
            {page < 3 && <View style={styles.line} />}
          </React.Fragment>
        ))}
      </View>

      {currentPage === 1 && (
        <View>
          <Text>Job Description (Upload File)</Text>
          <TouchableOpacity style={styles.uploadButton} onPress={() => handleFileChange('jobDescriptionFile')}>
            <Text>{formData.jobDescriptionFile ? 'File selected' : 'Select file'}</Text>
          </TouchableOpacity>

          {okta && (
            <View>
              <Text>Company Name</Text>
              <TextInput
                style={styles.input}
                value={formData.companyName}
                onChangeText={(text) => handleInputChange('companyName', text)}
              />
            </View>
          )}
          
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
      <ErrorModal
        visible={showErrorModal}
        errors={Object.values(formErrors).filter(Boolean) as string[]}
        onClose={() => setShowErrorModal(false)}
      />
    </ScrollView>
  );
};

export default Onboarding;