import Model from './model';


export default class Sound extends Model {
    get name() { return this.data.name }

    static getId(data) { return data.pk }
}


