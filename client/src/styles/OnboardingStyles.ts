import { StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  paginationContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  circle: {
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activeCircle: {
    backgroundColor: '#333',
  },
  inactiveCircle: {
    backgroundColor: '#aaa',
  },
  circleText: {
    color: 'white',
    fontSize: 16,
  },
  line: {
    width: 40,
    height: 2,
    backgroundColor: '#aaa',
    marginHorizontal: 10,
  },
  button: {
    padding: 10,
    paddingHorizontal: 20,
    backgroundColor: '#007bff',
    borderRadius: 5,
    marginTop: 20,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    padding: 10,
    marginBottom: 10,
  },
  textArea: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    padding: 10,
    marginBottom: 10,
    height: 100,
    textAlignVertical: 'top',
  },
  suggestionList: {
    marginTop: 5,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    maxHeight: 150,
  },
  suggestionItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  skillTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 10,
  },
  skillTag: {
    backgroundColor: '#e1e1e1',
    borderRadius: 20,
    padding: 5,
    paddingHorizontal: 10,
    margin: 5,
    flexDirection: 'row',
    alignItems: 'center',
  },
  skillTagText: {
    marginRight: 5,
  },
  removeSkillButton: {
    color: '#999',
    fontSize: 16,
    fontWeight: 'bold',
  },
  pageContainer: {
    padding: 20,
  },
  skillSection: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  uploadButton: {
    backgroundColor: '#007bff',
    borderRadius: 5,
    padding: 10,
    marginBottom: 10,
  },
});

export default styles;
