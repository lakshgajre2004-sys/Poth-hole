import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  View, 
  Text, 
  Alert, 
  ScrollView, 
  TouchableOpacity,
  Image,
  TextInput,
  Modal,
  ActivityIndicator
} from 'react-native';
import { Provider as PaperProvider, Button, Card, Title, Paragraph } from 'react-native-paper';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system';
import * as Network from 'expo-network';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:3000/api';

export default function App() {
  const [currentLocation, setCurrentLocation] = useState(null);
  const [address, setAddress] = useState('');
  const [issueType, setIssueType] = useState('pothole');
  const [severity, setSeverity] = useState('medium');
  const [description, setDescription] = useState('');
  const [photos, setPhotos] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userId, setUserId] = useState(null);
  const [isOffline, setIsOffline] = useState(false);
  const [pendingReports, setPendingReports] = useState([]);

  useEffect(() => {
    initializeApp();
    checkNetworkStatus();
  }, []);

  const initializeApp = async () => {
    try {
      // Request location permission
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied', 'Location permission is required to report issues');
        return;
      }

      // Get current location
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High
      });
      
      setCurrentLocation(location.coords);

      // Get address from coordinates
      const addresses = await Location.reverseGeocodeAsync({
        latitude: location.coords.latitude,
        longitude: location.coords.longitude
      });

      if (addresses.length > 0) {
        const addr = addresses[0];
        setAddress(`${addr.street || ''} ${addr.city || ''} ${addr.region || ''}`.trim());
      }

      // Get or create user ID
      let storedUserId = await AsyncStorage.getItem('userId');
      if (!storedUserId) {
        storedUserId = await createUser();
        await AsyncStorage.setItem('userId', storedUserId);
      }
      setUserId(storedUserId);

      // Load pending reports
      await loadPendingReports();

    } catch (error) {
      console.error('Error initializing app:', error);
      Alert.alert('Error', 'Failed to initialize app');
    }
  };

  const createUser = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/users/register`, {
        username: `User_${Date.now()}`,
        email: `user_${Date.now()}@example.com`,
        role: 'citizen'
      });
      return response.data.user.id;
    } catch (error) {
      console.error('Error creating user:', error);
      throw error;
    }
  };

  const checkNetworkStatus = async () => {
    const networkState = await Network.getNetworkStateAsync();
    setIsOffline(!networkState.isConnected);
  };

  const loadPendingReports = async () => {
    try {
      const stored = await AsyncStorage.getItem('pendingReports');
      if (stored) {
        setPendingReports(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Error loading pending reports:', error);
    }
  };

  const savePendingReport = async (reportData) => {
    try {
      const newPendingReports = [...pendingReports, {
        ...reportData,
        id: Date.now(),
        timestamp: new Date().toISOString()
      }];
      setPendingReports(newPendingReports);
      await AsyncStorage.setItem('pendingReports', JSON.stringify(newPendingReports));
    } catch (error) {
      console.error('Error saving pending report:', error);
    }
  };

  const removePendingReport = async (reportId) => {
    try {
      const newPendingReports = pendingReports.filter(r => r.id !== reportId);
      setPendingReports(newPendingReports);
      await AsyncStorage.setItem('pendingReports', JSON.stringify(newPendingReports));
    } catch (error) {
      console.error('Error removing pending report:', error);
    }
  };

  const syncPendingReports = async () => {
    if (pendingReports.length === 0) return;

    setIsSubmitting(true);
    try {
      for (const report of pendingReports) {
        await submitReport(report, false);
        await removePendingReport(report.id);
      }
      Alert.alert('Success', 'All pending reports have been synced');
    } catch (error) {
      console.error('Error syncing pending reports:', error);
      Alert.alert('Error', 'Failed to sync some reports');
    } finally {
      setIsSubmitting(false);
    }
  };

  const takePhoto = async () => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied', 'Camera permission is required to take photos');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        setPhotos([...photos, result.assets[0]]);
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo');
    }
  };

  const pickPhoto = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied', 'Photo library permission is required');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        allowsMultipleSelection: true,
      });

      if (!result.canceled && result.assets) {
        setPhotos([...photos, ...result.assets]);
      }
    } catch (error) {
      console.error('Error picking photo:', error);
      Alert.alert('Error', 'Failed to pick photo');
    }
  };

  const removePhoto = (index) => {
    setPhotos(photos.filter((_, i) => i !== index));
  };

  const submitReport = async (reportData = null, showAlert = true) => {
    const data = reportData || {
      type: issueType,
      latitude: currentLocation.latitude,
      longitude: currentLocation.longitude,
      address,
      severity,
      description,
      roadType: 'other',
      reporterId: userId
    };

    if (isOffline && !reportData) {
      // Save for later sync
      await savePendingReport(data);
      if (showAlert) {
        Alert.alert(
          'Report Saved Offline',
          'Your report has been saved and will be submitted when you have internet connection.',
          [{ text: 'OK' }]
        );
      }
      return;
    }

    try {
      const formData = new FormData();
      
      // Add report data
      Object.keys(data).forEach(key => {
        formData.append(key, data[key]);
      });

      // Add photos
      if (photos.length > 0) {
        photos.forEach((photo, index) => {
          formData.append('photos', {
            uri: photo.uri,
            type: 'image/jpeg',
            name: `photo_${index}.jpg`
          });
        });
      }

      const response = await axios.post(`${API_BASE_URL}/issues/report`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (showAlert) {
        if (response.data.isDuplicate) {
          Alert.alert(
            'Report Merged',
            'This issue was already reported nearby. Your report has been merged with the existing one.',
            [{ text: 'OK' }]
          );
        } else {
          Alert.alert(
            'Report Submitted',
            'Your report has been submitted successfully!',
            [{ text: 'OK' }]
          );
        }
      }

      // Reset form
      setDescription('');
      setPhotos([]);
      setSeverity('medium');

    } catch (error) {
      console.error('Error submitting report:', error);
      if (showAlert) {
        Alert.alert('Error', 'Failed to submit report. Please try again.');
      }
      throw error;
    }
  };

  const handleSubmit = async () => {
    if (!currentLocation) {
      Alert.alert('Error', 'Location not available');
      return;
    }

    if (!description.trim()) {
      Alert.alert('Error', 'Please provide a description');
      return;
    }

    setIsSubmitting(true);
    try {
      await submitReport();
    } catch (error) {
      // Error handling is done in submitReport
    } finally {
      setIsSubmitting(false);
    }
  };

  const getIssueTypeIcon = (type) => {
    switch (type) {
      case 'pothole': return '🕳️';
      case 'road_construction': return '🚧';
      case 'road_closure': return '🚫';
      default: return '📍';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'low': return '#4CAF50';
      case 'medium': return '#FF9800';
      case 'high': return '#F44336';
      case 'critical': return '#9C27B0';
      default: return '#FF9800';
    }
  };

  return (
    <PaperProvider>
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Report Road Issue</Text>
          {isOffline && (
            <View style={styles.offlineIndicator}>
              <Text style={styles.offlineText}>📡 Offline Mode</Text>
            </View>
          )}
        </View>

        {/* Issue Type Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Issue Type</Title>
            <View style={styles.typeContainer}>
              {[
                { key: 'pothole', label: 'Pothole', icon: '🕳️' },
                { key: 'road_construction', label: 'Road Construction', icon: '🚧' },
                { key: 'road_closure', label: 'Road Closure', icon: '🚫' }
              ].map((type) => (
                <TouchableOpacity
                  key={type.key}
                  style={[
                    styles.typeButton,
                    issueType === type.key && styles.typeButtonSelected
                  ]}
                  onPress={() => setIssueType(type.key)}
                >
                  <Text style={styles.typeIcon}>{type.icon}</Text>
                  <Text style={[
                    styles.typeLabel,
                    issueType === type.key && styles.typeLabelSelected
                  ]}>
                    {type.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </Card.Content>
        </Card>

        {/* Location Info */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Location</Title>
            <Text style={styles.locationText}>
              📍 {address || 'Getting location...'}
            </Text>
            {currentLocation && (
              <Text style={styles.coordinatesText}>
                Lat: {currentLocation.latitude.toFixed(6)}, 
                Lng: {currentLocation.longitude.toFixed(6)}
              </Text>
            )}
          </Card.Content>
        </Card>

        {/* Severity Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Severity</Title>
            <View style={styles.severityContainer}>
              {[
                { key: 'low', label: 'Low', color: '#4CAF50' },
                { key: 'medium', label: 'Medium', color: '#FF9800' },
                { key: 'high', label: 'High', color: '#F44336' },
                { key: 'critical', label: 'Critical', color: '#9C27B0' }
              ].map((sev) => (
                <TouchableOpacity
                  key={sev.key}
                  style={[
                    styles.severityButton,
                    { borderColor: sev.color },
                    severity === sev.key && { backgroundColor: sev.color }
                  ]}
                  onPress={() => setSeverity(sev.key)}
                >
                  <Text style={[
                    styles.severityLabel,
                    severity === sev.key && styles.severityLabelSelected
                  ]}>
                    {sev.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </Card.Content>
        </Card>

        {/* Description */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Description</Title>
            <TextInput
              style={styles.descriptionInput}
              placeholder="Describe the issue in detail..."
              value={description}
              onChangeText={setDescription}
              multiline
              numberOfLines={4}
            />
          </Card.Content>
        </Card>

        {/* Photo Section */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Photos ({photos.length}/5)</Title>
            <View style={styles.photoContainer}>
              {photos.map((photo, index) => (
                <View key={index} style={styles.photoItem}>
                  <Image source={{ uri: photo.uri }} style={styles.photo} />
                  <TouchableOpacity
                    style={styles.removePhotoButton}
                    onPress={() => removePhoto(index)}
                  >
                    <Text style={styles.removePhotoText}>×</Text>
                  </TouchableOpacity>
                </View>
              ))}
              {photos.length < 5 && (
                <TouchableOpacity style={styles.addPhotoButton} onPress={takePhoto}>
                  <Text style={styles.addPhotoText}>📷</Text>
                  <Text style={styles.addPhotoLabel}>Take Photo</Text>
                </TouchableOpacity>
              )}
            </View>
            {photos.length < 5 && (
              <Button mode="outlined" onPress={pickPhoto} style={styles.pickPhotoButton}>
                Pick from Gallery
              </Button>
            )}
          </Card.Content>
        </Card>

        {/* Submit Button */}
        <Button
          mode="contained"
          onPress={handleSubmit}
          disabled={isSubmitting || !currentLocation || !description.trim()}
          style={styles.submitButton}
          loading={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Report'}
        </Button>

        {/* Pending Reports */}
        {pendingReports.length > 0 && (
          <Card style={styles.card}>
            <Card.Content>
              <Title>Pending Reports ({pendingReports.length})</Title>
              {pendingReports.map((report) => (
                <View key={report.id} style={styles.pendingReport}>
                  <Text style={styles.pendingReportText}>
                    {getIssueTypeIcon(report.type)} {report.type.replace('_', ' ')} - {report.severity}
                  </Text>
                  <Text style={styles.pendingReportTime}>
                    {new Date(report.timestamp).toLocaleString()}
                  </Text>
                </View>
              ))}
              <Button mode="outlined" onPress={syncPendingReports} style={styles.syncButton}>
                Sync Pending Reports
              </Button>
            </Card.Content>
          </Card>
        )}
      </ScrollView>
    </PaperProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2196F3',
    padding: 20,
    paddingTop: 50,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
  },
  offlineIndicator: {
    backgroundColor: '#FF5722',
    padding: 8,
    borderRadius: 4,
    marginTop: 10,
    alignItems: 'center',
  },
  offlineText: {
    color: 'white',
    fontWeight: 'bold',
  },
  card: {
    margin: 10,
    elevation: 4,
  },
  typeContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
  },
  typeButton: {
    alignItems: 'center',
    padding: 10,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#ddd',
    minWidth: 80,
  },
  typeButtonSelected: {
    borderColor: '#2196F3',
    backgroundColor: '#E3F2FD',
  },
  typeIcon: {
    fontSize: 24,
    marginBottom: 5,
  },
  typeLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
  typeLabelSelected: {
    color: '#2196F3',
    fontWeight: 'bold',
  },
  locationText: {
    fontSize: 16,
    marginVertical: 5,
  },
  coordinatesText: {
    fontSize: 12,
    color: '#666',
  },
  severityContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
  },
  severityButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 2,
  },
  severityLabel: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  severityLabelSelected: {
    color: 'white',
  },
  descriptionInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
    textAlignVertical: 'top',
  },
  photoContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 10,
  },
  photoItem: {
    position: 'relative',
    margin: 5,
  },
  photo: {
    width: 80,
    height: 80,
    borderRadius: 8,
  },
  removePhotoButton: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: '#F44336',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removePhotoText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  addPhotoButton: {
    width: 80,
    height: 80,
    borderWidth: 2,
    borderColor: '#ddd',
    borderStyle: 'dashed',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    margin: 5,
  },
  addPhotoText: {
    fontSize: 24,
    marginBottom: 5,
  },
  addPhotoLabel: {
    fontSize: 10,
    textAlign: 'center',
  },
  pickPhotoButton: {
    marginTop: 10,
  },
  submitButton: {
    margin: 20,
    paddingVertical: 10,
  },
  pendingReport: {
    backgroundColor: '#FFF3E0',
    padding: 10,
    borderRadius: 8,
    marginVertical: 5,
  },
  pendingReportText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  pendingReportTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  syncButton: {
    marginTop: 10,
  },
});
